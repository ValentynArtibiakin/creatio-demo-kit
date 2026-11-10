// Local stand-in for the claude.ai runtime (db, user, sample), to test the edit layer of a built carousel before publishing.
// Loaded by .test-mock.html, which mock_test.py writes into the seed folder next to screens-seed/ and steps-seed/.
// URL switches: ?can=false (viewer cannot write), ?can=null (platform says nothing), ?fail=1 (every write is refused).
// Test hooks: window.__w (write log), window.__push(id, {html, css}) (a db update from another viewer),
// window.__answer = function(prompt){ return {summary, edits|html|css|steps} } (what "Claude" replies next).
// Test data only: nothing here talks to the network except the seed files next to the page.
window.__w = [];
(function () {
  var qs = new URLSearchParams(location.search);
  window.__fail = qs.get('fail') === '1';
  var can = qs.has('can') ? (qs.get('can') === 'null' ? null : qs.get('can') === 'true') : true;
  var store = {}, listeners = { screens: [], steps: [] };
  function snap(path, d) { return { id: path.split('/').pop(), exists: !!d, data: function () { return d && JSON.parse(JSON.stringify(d)) } } }
  function emit(c, keys) {
    var docs = keys.map(function (k) { return snap(k, store[k]) });
    listeners[c].forEach(function (n) { n({ docs: docs, empty: !docs.length, size: docs.length }) });
  }
  function docRef(p) {
    return {
      get: async function () { return snap(p, store[p]) },
      set: async function (d) {
        await new Promise(function (r) { setTimeout(r, 60) });
        if (window.__fail) throw { code: 'invalid_argument', message: 'refused by mock' };
        if (can === false) throw { code: 'permission_denied', message: 'viewer' };
        window.__w.push('set ' + p); store[p] = JSON.parse(JSON.stringify(d));
        var c = p.split('/')[0]; if (listeners[c]) emit(c, [p]);
      },
      delete: async function () { window.__w.push('delete ' + p); delete store[p] }
    };
  }
  function query(c) {
    var f = [], ord = null, lim = 1e9, q;
    q = {
      where: function (k, op, v) { f.push([k, v]); return q },
      orderBy: function (k, dir) { ord = [k, dir]; return q },
      limit: function (n) { lim = n; return q },
      get: async function () {
        var keys = Object.keys(store).filter(function (k) { return k.indexOf(c + '/') === 0 && f.every(function (x) { return store[k][x[0]] === x[1] }) });
        if (ord) keys.sort(function (a, b) { var x = store[a][ord[0]], y = store[b][ord[0]]; return (x < y ? -1 : x > y ? 1 : 0) * (ord[1] === 'desc' ? -1 : 1) });
        var docs = keys.slice(0, lim).map(function (k) { return snap(k, store[k]) });
        return { empty: !docs.length, docs: docs, size: docs.length };
      },
      onSnapshot: function (n) {
        listeners[c] = listeners[c] || []; listeners[c].push(n);
        if (c === 'screens' || c === 'steps') {
          var ids = (window.__wk && window.__wk.ids) || [];
          Promise.all(ids.map(function (id) {
            return fetch((c === 'screens' ? 'screens-seed/' : 'steps-seed/') + id + '.json').then(function (r) { return r.ok ? r.json() : null }, function () { return null })
              .then(function (d) { if (d) store[c + '/' + id] = d; return d ? c + '/' + id : null });
          })).then(function (keys) { emit(c, keys.filter(Boolean)); if (c === 'screens') window.__seedsLoaded = true });
        }
        return function () {};
      }
    };
    return q;
  }
  window.__push = function (id, d) { store['screens/' + id] = d; emit('screens', ['screens/' + id]) };
  window.__store = store;
  var db = { doc: docRef, collection: query };
  var user = { id: async function () { return 'u_test' }, can: async function () { return can } };
  // default answer: insert a marker right after the root tag of the screen
  var sample = {
    json: async function (prompt, opts) {
      await new Promise(function (r) { setTimeout(r, 80) });
      if (opts && opts.signal && opts.signal.aborted) throw { code: 'cancelled' };
      if (window.__answer) return window.__answer(prompt);
      var h = prompt.split('Current HTML:\n')[1].split('\n\nRequested change')[0], f = h.slice(0, h.indexOf('>') + 1);
      return { summary: 'Added a test marker', edits: [{ field: 'html', find: f, replace: f + '<b class="k-test" style="position:absolute;z-index:9;left:600px;top:300px;background:yellow;font-size:40px">TEST CHANGE</b>' }] };
    }
  };
  window.claude = { use: async function (n) { return n === 'db' ? db : n === 'user' ? user : n === 'sample' ? sample : null } };
})();
