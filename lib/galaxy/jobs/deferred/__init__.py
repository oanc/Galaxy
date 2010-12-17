"""
Queue for running deferred code via plugins.
"""
import os, sys, logging, threading
from Queue import Queue, Empty

from galaxy import model
from galaxy.util.bunch import Bunch

log = logging.getLogger( __name__ )

class DeferredJobQueue( object ):
    job_states = Bunch( READY = 'ready',
                        WAIT = 'wait', 
                        INVALID = 'invalid' )
    def __init__( self, app ):
        self.app = app
        self.sa_session = app.model.context
        self.queue = Queue()
        self.plugins = {}
        self._load_plugins()
        self.sleeper = Sleeper()
        self.running = True
        self.waiting_jobs = []
        self.__check_jobs_at_startup()
        self.monitor_thread = threading.Thread( target=self.__monitor )
        self.monitor_thread.start()
        log.info( 'Deferred job queue started' )

    def _load_plugins( self ):
        for fname in os.listdir( os.path.dirname( __file__ ) ):
            if not fname.startswith( '_' ) and fname.endswith( '.py' ):
                name = fname[:-3]
                module_name = 'galaxy.jobs.deferred.' + name
                try:
                    module = __import__( module_name )
                except:
                    log.exception( 'Deferred job plugin appears to exist but is not loadable: %s' % module_name )
                    continue
                for comp in module_name.split( "." )[1:]:
                    module = getattr( module, comp )
                if '__all__' not in dir( module ):
                    log.error( 'Plugin "%s" does not contain a list of exported classes in __all__' % module_name )
                    continue
                for obj in module.__all__:
                    display_name = ':'.join( ( module_name, obj ) )
                    plugin = getattr( module, obj )
                    for name in ( 'check_job', 'run_job' ):
                        if name not in dir( plugin ):
                            log.error( 'Plugin "%s" does not contain required method "%s()"' % ( display_name, name ) )
                            break
                    else:
                        self.plugins[obj] = plugin( self.app )
                        self.plugins[obj].job_states = self.job_states
                        log.debug( 'Loaded deffered job plugin: %s' % display_name )

    def __check_jobs_at_startup( self ):
        waiting_jobs = self.sa_session.query( model.DeferredJob ) \
                                      .filter( model.DeferredJob.state == model.DeferredJob.states.WAITING ).all()
        for job in waiting_jobs:
            if not self.__check_job_plugin( job ):
                continue
            if 'check_interval' in dir( self.plugins[job.plugin] ):
                job.check_interval = self.plugins[job.plugin].check_interval
            log.info( 'Recovered deferred job (id: %s) at startup' % job.id )
            self.waiting_jobs.append( job )

    def __monitor( self ):
        while self.running:
            try:
                self.__monitor_step()
            except:
                log.exception( 'Exception in monitor_step' )
            self.sleeper.sleep( 1 )
        log.info( 'job queue stopped' )

    def __monitor_step( self ):
        # TODO: Querying the database with this frequency is bad, we need message passing
        new_jobs = self.sa_session.query( model.DeferredJob ) \
                                  .filter( model.DeferredJob.state == model.DeferredJob.states.NEW ).all()
        for job in new_jobs:
            if not self.__check_job_plugin( job ):
                continue
            job.state = model.DeferredJob.states.WAITING
            self.sa_session.add( job )
            self.sa_session.flush()
            if 'check_interval' in dir( self.plugins[job.plugin] ):
                job.check_interval = self.plugins[job.plugin].check_interval
            self.waiting_jobs.append( job )
        new_waiting = []
        for job in self.waiting_jobs:
            if job.is_check_time:
                try:
                    job_state = self.plugins[job.plugin].check_job( job )
                except:
                    raise # TODO: fail
                if job_state == self.job_states.READY:
                    try:
                        self.plugins[job.plugin].run_job( job )
                    except:
                        raise # TODO: fail
                elif job_state == self.job_states.INVALID:
                    # TODO: fail
                    log.error( 'Unable to run deferred job (id: %s): Plugin "%s" marked it as invalid' % ( job.id, job.plugin ) )
                else:
                    new_waiting.append( job )
                job.last_check = 'now'
            else:
                new_waiting.append( job )
        self.waiting_jobs = new_waiting

    def __check_job_plugin( self, job ):
        if job.plugin not in self.plugins:
            log.error( 'Invalid deferred job plugin: %s' ) % job.plugin
            job.state = model.DeferredJob.states.ERROR
            job.info = 'Invalid deferred job plugin: %s' % job.plugin
            self.sa_session.add( job )
            self.sa_session.flush()
            return False
        return True

    def __check_if_ready_to_run( self, job ):
        return self.plugins[job.plugin].check_job( job )

    def shutdown( self ):
        self.running = False
        self.sleeper.wake()

class Sleeper( object ):
    """
    Provides a 'sleep' method that sleeps for a number of seconds *unless*
    the notify method is called (from a different thread).
    """
    def __init__( self ):
        self.condition = threading.Condition()
    def sleep( self, seconds ):
        self.condition.acquire()
        self.condition.wait( seconds )
        self.condition.release()
    def wake( self ):
        self.condition.acquire()
        self.condition.notify()
        self.condition.release()