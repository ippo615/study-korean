let html = '';
for( let i=0, l=phrases.length; i<l; i+=1 ){
	let phrase = phrases[i];
	html += '<section>';
	html += '<section><h1>'+phrase.korean+'</h1></section>';
	html += '<section><h1>'+phrase.english+'</h1></section>';
	html += '</section>';
}
document.getElementById('main').innerHTML = html;
