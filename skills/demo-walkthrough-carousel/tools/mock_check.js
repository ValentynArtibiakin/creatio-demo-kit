// Paste into the browser console (or javascript_exec) on .test-mock.html?run=N#<ScreenId>, with the default switches.
// Checks the edit layer end to end and that hostile HTML/CSS from Claude or from the db never becomes active.
// Result: {pass, fails[], writes[]}.
(async function () {
  var fails = [], $ = function (s) { return document.querySelector(s) }, wait = function (ms) { return new Promise(function (r) { setTimeout(r, ms) }) };
  function ok(c, msg) { if (!c) fails.push(msg) }
  for (var i = 0; i < 50 && !window.__seedsLoaded; i++) await wait(100);
  await wait(300);
  var W = window.__wk, id = W.curId(), scr = function () { return $('#s-' + id) };
  ok(window.__seedsLoaded, 'seed screens did not load');
  ok(!$('#t-hot').checked && !$('#t-tags').checked, 'Show clickable / Build labels must start unchecked');
  ok(!$('#chat-fab').hidden, 'Change with Claude button is hidden');
  ok(!$('#t-edit').hidden, 'Edit step text button is hidden for a writer');
  ok(!$('#t-gap').hidden && /\d/.test($('#t-gap').textContent), 'Gaps & blockers button missing');
  ok(scr().querySelector('a[data-go]') || !document.querySelectorAll('a[data-go]').length, 'links to other screens lost after the db redraw');

  // 1. a normal change is drawn and saved with a version copy
  async function ask(t) { $('#chat-fab').click(); $('#chat-ta').value = t; $('#chat-form').requestSubmit(); await wait(700) }
  var before = window.__w.length;
  await ask('add a marker');
  ok(/TEST CHANGE/.test(scr().innerHTML), 'the change was not drawn');
  var w = window.__w.slice(before).join(' | ');
  ok(/set screen_versions\//.test(w) && /set screens\//.test(w), 'save did not write screen_versions + screens: ' + w);
  ok($('#pend').hidden, 'pending bar still shown after a good save');

  // 2. undo brings the previous version back
  [].slice.call(document.querySelectorAll('#chat-acts button')).filter(function (b) { return /Undo/.test(b.textContent) })[0].click();
  await wait(500);
  ok(!/TEST CHANGE/.test(scr().innerHTML), 'undo did not restore the previous version');

  // 3. hostile answers from Claude
  window.__pwned = 0;
  var evil = [
    { summary: 'x', edits: [{ field: 'html', find: '>', replace: '><img src=x onerror="window.__pwned=1">' }] },
    { summary: 'x', edits: [{ field: 'html', find: '>', replace: '><a href="jav&#x61;script:window.__pwned=2">x</a><iframe srcdoc="<script>parent.__pwned=3</script>"></iframe><svg><a><animate attributeName="href" values="jav&#x61;script:parent.__pwned=4"/><text y="20">y</text></a></svg><object data="data:text/html,x"></object><form action="https://example.com"><input></form>' }] },
    { summary: 'x', edits: [{ field: 'css', find: '', replace: '' }], css: '' }
  ];
  window.__answer = function () { return evil[0] }; await ask('evil 1');
  ok(!scr().querySelector('[onerror]') && window.__pwned === 0, 'onerror handler reached the page');
  window.__answer = function (p) { var h = p.split('Current HTML:\n')[1]; var f = h.slice(0, h.indexOf('>') + 1); var e = JSON.parse(JSON.stringify(evil[1])); e.edits[0].find = f; e.edits[0].replace = f + e.edits[0].replace.slice(1); return e };
  await ask('evil 2');
  var s = scr();
  ok(!s.querySelector('iframe,object,embed,form,script,animate,set'), 'active element survived: ' + (s.querySelector('iframe,object,embed,form,script,animate,set') || {}).outerHTML);
  ok(![].some.call(s.querySelectorAll('[href]'), function (a) { return /^\s*javascript:/i.test(a.getAttribute('href')) }), 'javascript: link survived');
  window.__answer = function (p) { var h = p.split('Current HTML:\n')[1].split('\n\nRequested change')[0]; return { summary: 'x', html: h, css: 'body{background:url(https://example.com/x.png)} @import "https://example.com/a.css"; .k-x{width:expression(alert(1))}' } };
  await ask('evil css');
  var css = ($('#css-' + id) || {}).textContent || '';
  ok(!/url\(\s*['"]?https?:|@import|expression\(/i.test(css), 'hostile CSS survived: ' + css.slice(0, 200));
  window.__answer = null;

  // 4. hostile screen arriving from the db (another viewer, or a hand-made write)
  window.__push(id, { html: '<div class="{{tagsClass}}"><img src=x onerror="window.__pwned=5"><a href="javascript:window.__pwned=6">a</a><iframe src="https://example.com"></iframe><div style="background:url(javascript:alert(1))">s</div></div>', css: '' });
  await wait(300);
  s = scr();
  ok(!s.querySelector('[onerror],iframe') && !/javascript:/i.test(s.innerHTML), 'hostile db screen survived: ' + s.innerHTML.slice(0, 200));
  await wait(200);
  ok(window.__pwned === 0, 'a payload ran (__pwned=' + window.__pwned + ')');

  // 5. manual step editor saves for everyone
  $('#t-edit').click(); await wait(100);
  var ta = $('#editor textarea'); if (ta) { ta.value = 'Edited by the mock test'; ta.dispatchEvent(new Event('input')) }
  before = window.__w.length;
  [].slice.call(document.querySelectorAll('#editor button')).filter(function (b) { return /Save for everyone/.test(b.textContent) })[0].click();
  await wait(300);
  ok(/set steps\//.test(window.__w.slice(before).join(' ')), 'step editor did not write steps/' + id);
  $('#t-edit').click();

  return { pass: !fails.length, fails: fails, writes: window.__w };
})();
