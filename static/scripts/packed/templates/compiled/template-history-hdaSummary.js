(function(){var b=Handlebars.template,a=Handlebars.templates=Handlebars.templates||{};a["template-history-hdaSummary"]=b(function(g,n,f,m,l){f=f||g.helpers;var j="",d,i,h="function",k=this.escapeExpression,o=this;function e(t,s){var q="",r,p;q+='\n    <a href="';p=f.edit_url;if(p){r=p.call(t,{hash:{}})}else{r=t.edit_url;r=typeof r===h?r():r}q+=k(r)+'" target="galaxy_main">';p=f.metadata_dbkey;if(p){r=p.call(t,{hash:{}})}else{r=t.metadata_dbkey;r=typeof r===h?r():r}q+=k(r)+"</a>\n";return q}function c(t,s){var q="",r,p;q+='\n    <span class="';p=f.metadata_dbkey;if(p){r=p.call(t,{hash:{}})}else{r=t.metadata_dbkey;r=typeof r===h?r():r}q+=k(r)+'">';p=f.metadata_dbkey;if(p){r=p.call(t,{hash:{}})}else{r=t.metadata_dbkey;r=typeof r===h?r():r}q+=k(r)+"</span>\n";return q}i=f.misc_blurb;if(i){d=i.call(n,{hash:{}})}else{d=n.misc_blurb;d=typeof d===h?d():d}j+=k(d)+'<br />\nformat: <span class="';i=f.data_type;if(i){d=i.call(n,{hash:{}})}else{d=n.data_type;d=typeof d===h?d():d}j+=k(d)+'">';i=f.data_type;if(i){d=i.call(n,{hash:{}})}else{d=n.data_type;d=typeof d===h?d():d}j+=k(d)+"</span>,\ndatabase:\n";d=n.dbkey_unknown_and_editable;d=f["if"].call(n,d,{hash:{},inverse:o.program(3,c,l),fn:o.program(1,e,l)});if(d||d===0){j+=d}return j})})();