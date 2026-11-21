/* Pokémon Origin Jade - player documentation. Enhancements only: every page
   reads fine without this file. No dependencies, works from file://.
   Parts: theme, language, menu, search, filter bars, tabs, outline.        */
(function () {
  "use strict";
  var doc = document, html = doc.documentElement;
  var lang = html.getAttribute("data-lang") || "de";
  var root = html.getAttribute("data-root") || "";
  var assets = root + "../assets/";
  var T = (/*@STRINGS@*/{})[lang] || {};

  function $(sel, el) { return (el || doc).querySelector(sel); }
  function $$(sel, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(sel)); }
  function el(tag, cls, text) {
    var e = doc.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (e) { /* private mode, file:// restrictions */ }
    return null;
  }
  function fmt(s, vars) {
    return String(s || "").replace(/\{(\w+)\}/g, function (m, k) { return k in vars ? vars[k] : m; });
  }

  /* ---- text folding: keep in step with common/search.py fold() ---- */
  var UML = { "ä": "ae", "ö": "oe", "ü": "ue" };
  function fold(s) {
    s = String(s).toLowerCase().replace(/ß/g, "ss");
    if (s.normalize) s = s.normalize("NFD").replace(/[̀-ͯ]/g, "");
    return s.replace(/[^a-z0-9]+/g, " ").trim();
  }
  function altFold(s) {
    var low = String(s).toLowerCase();
    if (!/[äöü]/.test(low)) return "";
    return fold(low.replace(/[äöü]/g, function (c) { return UML[c]; }));
  }

  /* ---- theme ---- */
  function currentTheme() {
    var t = html.getAttribute("data-theme");
    if (t === "light" || t === "dark") return t;
    return window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  $$("[data-theme-toggle]").forEach(function (b) {
    b.setAttribute("aria-pressed", currentTheme() === "dark" ? "true" : "false");
    b.addEventListener("click", function () {
      var t = currentTheme() === "dark" ? "light" : "dark";
      html.setAttribute("data-theme", t);
      store("oj-theme", t);
      b.setAttribute("aria-pressed", t === "dark" ? "true" : "false");
    });
  });

  /* ---- language: same page in the other tree, keep query and hash, remember ---- */
  $$("a[data-lang]").forEach(function (a) {
    a.addEventListener("click", function () {
      store("oj-lang", a.getAttribute("data-lang"));
      a.href = a.getAttribute("href").split(/[?#]/)[0] + location.search + location.hash;
    });
  });

  /* ---- menu (phones and tablets): the sidebar becomes a drawer ---- */
  var menuBtn = $("[data-menu]"), nav = $("#nav"), page = $("#main");
  if (menuBtn && nav) {
    var scrim = el("div", "scrim");
    doc.body.appendChild(scrim);
    menuBtn.setAttribute("role", "button");
    menuBtn.setAttribute("aria-expanded", "false");
    menuBtn.setAttribute("aria-controls", "nav");
    var setMenu = function (open) {
      html.classList.toggle("nav-open", open);
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
      menuBtn.setAttribute("aria-label", open ? T.menu_close : T.menu);
      if (page) { if (open) page.setAttribute("inert", ""); else page.removeAttribute("inert"); }
      if (open) {
        var first = $("[aria-current]", nav) || $("a, summary", nav);
        if (first) first.focus();
      } else if (nav.contains(doc.activeElement)) {
        menuBtn.focus();
      }
    };
    menuBtn.addEventListener("click", function (e) {
      e.preventDefault();
      setMenu(!html.classList.contains("nav-open"));
    });
    menuBtn.addEventListener("keydown", function (e) {
      if (e.key === " ") { e.preventDefault(); menuBtn.click(); }
    });
    scrim.addEventListener("click", function () { setMenu(false); });
    doc.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && html.classList.contains("nav-open")) setMenu(false);
    });
    if (window.matchMedia) {
      var wide = matchMedia("(min-width: 68.75rem)");
      var onWide = function () { if (wide.matches && html.classList.contains("nav-open")) setMenu(false); };
      if (wide.addEventListener) wide.addEventListener("change", onWide); else if (wide.addListener) wide.addListener(onWide);
    }
  }

  /* ---- search: command palette over the whole site ---- */
  var search = (function () {
    var dlg, input, list, entries = null, state = "idle", active = -1, options = [], lastFocus = null, waiting = "";
    var PER_GROUP = 7, SINGLE = 40;

    function build() {
      dlg = el("dialog", "search");
      dlg.setAttribute("aria-label", T.search);
      var top = el("div", "search-top");
      var ic = el("span", "i i-search");
      ic.setAttribute("aria-hidden", "true");
      input = el("input", "search-in");
      input.type = "search";
      input.placeholder = T.search_placeholder;
      input.autocomplete = "off";
      input.spellcheck = false;
      input.setAttribute("role", "combobox");
      input.setAttribute("aria-label", T.search);
      input.setAttribute("aria-expanded", "true");
      input.setAttribute("aria-controls", "search-list");
      input.setAttribute("aria-autocomplete", "list");
      var x = el("button", "search-x", "Esc");
      x.type = "button";
      x.setAttribute("aria-label", T.close);
      top.appendChild(ic); top.appendChild(input); top.appendChild(x);
      list = el("div", "search-list");
      list.id = "search-list";
      list.setAttribute("role", "listbox");
      list.setAttribute("aria-label", T.search_results);
      var foot = el("div", "search-foot");
      foot.setAttribute("aria-hidden", "true");
      [["↑↓", T.search_keys_move], ["↵", T.search_keys_open], ["Esc", T.search_keys_close]].forEach(function (k) {
        var s = el("span");
        s.appendChild(el("kbd", "", k[0]));
        s.appendChild(doc.createTextNode(k[1]));
        foot.appendChild(s);
      });
      dlg.appendChild(top); dlg.appendChild(list); dlg.appendChild(foot);
      doc.body.appendChild(dlg);
      x.addEventListener("click", close);
      dlg.addEventListener("click", function (e) { if (e.target === dlg) close(); });
      dlg.addEventListener("close", function () {
        html.classList.remove("search-open");
        if (lastFocus && lastFocus.focus) lastFocus.focus();
      });
      dlg.addEventListener("cancel", function () { /* Esc: native close */ });
      input.addEventListener("input", function () { run(input.value); });
      input.addEventListener("keydown", onKey);
      list.addEventListener("mousemove", function (e) {
        var o = e.target.closest ? e.target.closest(".search-o") : null;
        if (o) select(options.indexOf(o), false);
      });
    }

    function message(text) {
      list.textContent = "";
      list.appendChild(el("p", "search-msg", text));
      options = []; active = -1;
      input.removeAttribute("aria-activedescendant");
    }

    function load() {
      if (state !== "idle") return;
      state = "loading";
      var s = doc.createElement("script");
      s.src = assets + "search-" + lang + ".js";
      s.onload = function () {
        var d = window.OJ_SEARCH;
        if (!d || !d.e) { state = "failed"; message(T.search_failed); return; }
        entries = d.e.map(function (r, i) {
          var f = fold(r[0]);
          return { t: r[0], k: r[1], u: r[2], i: r[4] || "", s: r[5] || "", f: f, a: altFold(r[0]),
            w: fold((r[3] || "") + " " + (r[5] || "")), n: i };
        });
        entries.kinds = d.kinds;
        state = "ready";
        run(waiting);
      };
      s.onerror = function () { state = "failed"; message(T.search_failed); };
      doc.head.appendChild(s);
    }

    /* score of one token against a folded text: 0 exact, 1 prefix, 2 word start, 3 inside, -1 none */
    function hit(text, tok) {
      var p = text.indexOf(tok);
      if (p < 0) return -1;
      if (p === 0) return text.length === tok.length ? 0 : 1;
      if (text.indexOf(" " + tok) >= 0) return 2;
      return 3;
    }
    function score(e, toks, whole) {
      if (e.f === whole || (e.a && e.a === whole)) return 0;
      var total = 0;
      for (var i = 0; i < toks.length; i++) {
        var s = hit(e.f, toks[i]);
        if (e.a) { var s2 = hit(e.a, toks[i]); if (s2 >= 0 && (s < 0 || s2 < s)) s = s2; }
        if (s < 0) {
          var k = e.w ? hit(e.w, toks[i]) : -1;
          if (k < 0) return -1;
          s = k <= 2 ? 5 : 6;
        } else {
          s += 1;
        }
        total += s;
      }
      return total;
    }

    function mark(node, title, toks) {
      /* bold the first place a token starts a word (plain text nodes only) */
      var low = title.toLowerCase(), best = -1, len = 0;
      toks.forEach(function (t) {
        var p = low.indexOf(t);
        if (p >= 0 && (best < 0 || p < best)) { best = p; len = t.length; }
      });
      if (best < 0) { node.textContent = title; return; }
      node.appendChild(doc.createTextNode(title.slice(0, best)));
      node.appendChild(el("mark", "", title.slice(best, best + len)));
      node.appendChild(doc.createTextNode(title.slice(best + len)));
    }

    function run(q) {
      waiting = q;
      if (state === "idle") { message(T.search_loading); load(); return; }
      if (state === "loading") { message(T.search_loading); return; }
      if (state === "failed") { message(T.search_failed); return; }
      var whole = fold(q);
      if (!whole) { message(T.search_hint); return; }
      var toks = whole.split(" "), found = [], i, e, s;
      for (i = 0; i < entries.length; i++) {
        e = entries[i];
        s = score(e, toks, whole);
        if (s >= 0) found.push({ e: e, s: s });
      }
      if (!found.length) { message(fmt(T.search_none, { q: q.trim() })); return; }
      found.sort(function (a, b) { return a.s - b.s || a.e.t.length - b.e.t.length || a.e.n - b.e.n; });
      var groups = {}, order = [];
      found.forEach(function (r) {
        if (!groups[r.e.k]) { groups[r.e.k] = []; order.push(r.e.k); }
        groups[r.e.k].push(r);
      });
      order.sort(function (a, b) { return groups[a][0].s - groups[b][0].s || a - b; });
      var limit = order.length === 1 ? SINGLE : PER_GROUP;
      list.textContent = "";
      options = [];
      order.forEach(function (k) {
        var g = el("div");
        g.setAttribute("role", "group");
        var label = el("p", "search-g", T["kind_" + entries.kinds[k]] || "");
        label.id = "search-g" + k;
        g.setAttribute("aria-labelledby", label.id);
        g.appendChild(label);
        groups[k].slice(0, limit).forEach(function (r) {
          var a = el("a", "search-o");
          a.href = root + r.e.u;
          a.id = "search-o" + options.length;
          a.setAttribute("role", "option");
          a.setAttribute("aria-selected", "false");
          a.tabIndex = -1;
          if (r.e.i) {
            var im = doc.createElement("img");
            im.src = assets + r.e.i;
            im.alt = "";
            im.className = "px" + (r.e.i.indexOf("item/") === 0 ? " s-item" : "");
            im.width = im.height = r.e.i.indexOf("item/") === 0 ? 24 : 32;
            a.appendChild(im);
          } else {
            a.appendChild(el("span", "search-ph"));
          }
          var b = el("b");
          mark(b, r.e.t, toks);
          a.appendChild(b);
          if (r.e.s) a.appendChild(el("span", "search-s", r.e.s));
          g.appendChild(a);
          options.push(a);
        });
        if (groups[k].length > limit) g.appendChild(el("p", "search-more", fmt(T.search_more, { n: groups[k].length - limit })));
        list.appendChild(g);
      });
      list.scrollTop = 0;
      select(0, false);
    }

    function select(i, scroll) {
      if (i < 0 || i >= options.length) return;
      if (active >= 0 && options[active]) options[active].setAttribute("aria-selected", "false");
      active = i;
      options[i].setAttribute("aria-selected", "true");
      input.setAttribute("aria-activedescendant", options[i].id);
      if (scroll && options[i].scrollIntoView) options[i].scrollIntoView({ block: "nearest" });
    }

    function onKey(e) {
      if (e.key === "Escape") { e.preventDefault(); close(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); select(Math.min(active + 1, options.length - 1), true); }
      else if (e.key === "ArrowUp") { e.preventDefault(); select(Math.max(active - 1, 0), true); }
      else if (e.key === "Home" && options.length && !input.value) { e.preventDefault(); select(0, true); }
      else if (e.key === "Enter") {
        e.preventDefault();
        if (active >= 0 && options[active]) {
          if (e.ctrlKey || e.metaKey) window.open(options[active].href, "_blank");
          else location.href = options[active].href;
        }
      }
    }

    function open() {
      if (!dlg) build();
      if (dlg.open) { input.focus(); input.select(); return; }
      lastFocus = doc.activeElement;
      html.classList.add("search-open");
      if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
      input.focus();
      input.select();
      run(input.value);
    }
    function close() {
      if (!dlg) return;
      if (dlg.close) dlg.close(); else { dlg.removeAttribute("open"); html.classList.remove("search-open"); }
    }
    return { open: open, close: close };
  })();

  $$("[data-search-open]").forEach(function (b) {
    b.addEventListener("click", function () { search.open(); });
  });
  doc.addEventListener("keydown", function (e) {
    var k = e.key;
    if ((k === "k" || k === "K") && (e.ctrlKey || e.metaKey) && !e.altKey) { e.preventDefault(); search.open(); return; }
    if (k === "/" && !e.ctrlKey && !e.metaKey && !e.altKey) {
      var t = e.target, tag = t && t.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (t && t.isContentEditable)) return;
      e.preventDefault();
      search.open();
    }
  });

  /* ---- filter bars ---- */
  $$("form[data-filter]").forEach(function (form) {
    var target = doc.getElementById(form.getAttribute("data-filter"));
    if (!target) return;
    var nodes = $$("[data-text]", target);
    var items = nodes.map(function (n) { return { n: n, t: " " + n.getAttribute("data-text") + " ", g: n.closest ? n.closest("[data-group]") : null }; });
    var groups = $$("[data-group]", target);
    if (target.hasAttribute("data-group")) groups.push(target);
    var text = $("input[name=q]", form), selects = $$("select", form), chipsets = $$(".filter-chips", form);
    var count = $(".filter-count", form), reset = $(".filter-reset", form);
    var none = el("p", "filter-none", T.filter_none);
    none.hidden = true;
    target.parentNode.insertBefore(none, target.nextSibling);
    var facets = {};
    var timer = 0;

    function chipValue(set) {
      var b = $("button[aria-pressed=true]", set);
      return b ? b.getAttribute("data-value") : "";
    }
    /* select options bound to a region are only offered for the chosen region */
    function regionOptions() {
      var region = "";
      chipsets.forEach(function (s) { if (s.getAttribute("data-key") === "region") region = chipValue(s); });
      selects.forEach(function (s) {
        $$("option[data-region]", s).forEach(function (o) {
          var off = !!region && o.getAttribute("data-region") !== region;
          o.hidden = off;
          o.disabled = off;
          if (off && o.selected) s.value = "";
        });
      });
    }
    function apply() {
      regionOptions();
      var toks = text ? fold(text.value).split(" ").filter(Boolean) : [];
      var keys = [];
      selects.forEach(function (s) { facets[s.name] = s.value; });
      chipsets.forEach(function (s) { facets[s.getAttribute("data-key")] = chipValue(s); });
      for (var k in facets) if (facets[k]) keys.push(k);
      var shown = 0, i, j, it, ok, v;
      for (i = 0; i < items.length; i++) {
        it = items[i];
        ok = true;
        for (j = 0; ok && j < toks.length; j++) if (it.t.indexOf(toks[j]) < 0) ok = false;
        for (j = 0; ok && j < keys.length; j++) {
          v = it.n.getAttribute("data-" + keys[j]);
          if (!v || (" " + v + " ").indexOf(" " + facets[keys[j]] + " ") < 0) ok = false;
        }
        if (it.n.hidden === ok) it.n.hidden = !ok;
        if (ok) shown++;
      }
      groups.forEach(function (g) {
        if (g === target) return;
        g.hidden = !$("[data-text]:not([hidden])", g);
      });
      var filtered = toks.length > 0 || keys.length > 0;
      /* groups that start folded open while a filter is set, and fold again without one */
      if (filtered !== target.classList.contains("is-filtered")) {
        target.classList.toggle("is-filtered", filtered);
        $$(".letters a[aria-current]").forEach(function (a) { a.removeAttribute("aria-current"); });
        $$(".start-closed", target).forEach(function (g) {
          g.classList.toggle("is-closed", !filtered);
          var h = g.firstElementChild;
          if (h) h.setAttribute("aria-expanded", filtered ? "true" : "false");
        });
        try { target.dispatchEvent(new CustomEvent("oj-filter", { detail: filtered })); } catch (e) { /* old browsers */ }
      }
      if (count) count.textContent = fmt(T.filter_count, { shown: shown, total: items.length });
      if (reset) reset.hidden = !filtered;
      none.hidden = shown > 0;
      try {
        var p = new URLSearchParams(location.search);
        if (text) { if (text.value.trim()) p.set("q", text.value.trim()); else p.delete("q"); }
        for (k in facets) { if (facets[k]) p.set(k, facets[k]); else p.delete(k); }
        var qs = p.toString();
        history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "") + location.hash);
      } catch (e) { /* file:// may refuse; the filter still works */ }
    }
    function later() { clearTimeout(timer); timer = setTimeout(apply, 60); }

    try {
      var p0 = new URLSearchParams(location.search);
      if (text && p0.get("q")) text.value = p0.get("q");
      selects.forEach(function (s) { if (p0.get(s.name)) s.value = p0.get(s.name); });
      chipsets.forEach(function (set) {
        var v = p0.get(set.getAttribute("data-key"));
        if (v) $$("button", set).forEach(function (b) { if (b.getAttribute("data-value") === v) b.setAttribute("aria-pressed", "true"); });
      });
    } catch (e) { /* no URL state */ }
    if (text) text.addEventListener("input", later);
    selects.forEach(function (s) { s.addEventListener("change", apply); });
    chipsets.forEach(function (set) {
      set.addEventListener("click", function (e) {
        var b = e.target.closest ? e.target.closest("button") : null;
        if (!b) return;
        var on = b.getAttribute("aria-pressed") === "true";
        $$("button", set).forEach(function (o) { o.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", on ? "false" : "true");
        apply();
      });
    });
    form.addEventListener("submit", function (e) { e.preventDefault(); apply(); });
    form.addEventListener("reset", function () {
      chipsets.forEach(function (set) { $$("button", set).forEach(function (o) { o.setAttribute("aria-pressed", "false"); }); });
      setTimeout(apply, 0);
    });
    form.hidden = false;
    apply();
  });

  /* ---- tabs: headings become a tab list ---- */
  var tabsets = $$("[data-tabs]").map(function (box) {
    var panels = $$(":scope > .tab", box);
    if (panels.length < 2) return null;
    var bar = el("div", "tablist");
    bar.setAttribute("role", "tablist");
    if (box.getAttribute("aria-label")) bar.setAttribute("aria-label", box.getAttribute("aria-label"));
    var tabs = panels.map(function (p, i) {
      var h = $(".tab-h", p);
      var b = el("button", "", h ? h.textContent : String(i + 1));
      b.type = "button";
      b.id = p.id + "-tab";
      b.setAttribute("role", "tab");
      b.setAttribute("aria-controls", p.id);
      p.setAttribute("role", "tabpanel");
      p.setAttribute("aria-labelledby", b.id);
      b.addEventListener("click", function () { show(i, false); });
      bar.appendChild(b);
      return b;
    });
    function show(n, focus) {
      panels.forEach(function (p, i) {
        p.hidden = i !== n;
        tabs[i].setAttribute("aria-selected", i === n ? "true" : "false");
        tabs[i].tabIndex = i === n ? 0 : -1;
      });
      if (focus) tabs[n].focus();
    }
    bar.addEventListener("keydown", function (e) {
      var i = tabs.indexOf(doc.activeElement), n = -1;
      if (i < 0) return;
      if (e.key === "ArrowRight") n = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft") n = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") n = 0;
      else if (e.key === "End") n = tabs.length - 1;
      if (n >= 0) { e.preventDefault(); show(n, true); }
    });
    box.insertBefore(bar, panels[0]);
    box.classList.add("is-on");
    show(0, false);
    return { panels: panels, show: show };
  }).filter(Boolean);
  /* ---- section tabs: the main sections of a page, one at a time ---- */
  var secTabs = (function () {
    var body = $("body:not(.home):not(.no-tabs) .page-body");
    if (!body) return null;
    var secs = $$(".sec", body).filter(function (s) {
      return s.parentNode === body && s.id && s.firstElementChild && s.firstElementChild.tagName === "H2";
    });
    if (secs.length < 2) return null;
    /* a page that fits on the screen anyway keeps its sections below each other */
    if (body.offsetHeight < window.innerHeight * 0.8) return null;
    /* a filter bar that spans several sections needs all of them on screen */
    var spans = $$("form[data-filter]").some(function (f) {
      var t = doc.getElementById(f.getAttribute("data-filter"));
      return t && secs.filter(function (s) { return t === s || t.contains(s); }).length > 1;
    });
    if (spans) return null;
    var bar = el("div", "tablist sectabs");
    bar.setAttribute("role", "tablist");
    var tabs = secs.map(function (s, i) {
      var b = el("button", "", s.firstElementChild.textContent);
      b.type = "button";
      b.id = s.id + "-sectab";
      b.setAttribute("role", "tab");
      b.setAttribute("aria-controls", s.id);
      s.setAttribute("role", "tabpanel");
      s.setAttribute("aria-labelledby", b.id);
      b.addEventListener("click", function () {
        show(i, false);
        try { history.replaceState(null, "", location.pathname + location.search + "#" + s.id); } catch (e) { /* file:// */ }
      });
      bar.appendChild(b);
      return b;
    });
    function show(n, focus) {
      secs.forEach(function (s, i) {
        s.hidden = i !== n;
        tabs[i].setAttribute("aria-selected", i === n ? "true" : "false");
        tabs[i].tabIndex = i === n ? 0 : -1;
      });
      if (focus) tabs[n].focus();
    }
    bar.addEventListener("keydown", function (e) {
      var i = tabs.indexOf(doc.activeElement), n = -1;
      if (i < 0) return;
      if (e.key === "ArrowRight") n = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft") n = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") n = 0;
      else if (e.key === "End") n = tabs.length - 1;
      if (n >= 0) { e.preventDefault(); show(n, true); }
    });
    body.insertBefore(bar, secs[0]);
    body.classList.add("is-tabbed");
    if (page) page.classList.add("has-tabs");
    show(0, false);
    return { secs: secs, show: show };
  })();
  /* ---- sections fold: click a heading to hide or show its section ---- */
  var folds = $$("body:not(.home) .page-body .sec > h2, body:not(.home) .page-body .sub > h3").filter(function (h) {
    return !secTabs || secTabs.secs.indexOf(h.parentNode) < 0;
  }).map(function (h) {
    var box = h.parentNode;
    h.setAttribute("role", "button");
    h.tabIndex = 0;
    h.classList.add("fold-h");
    function set(open) {
      box.classList.toggle("is-closed", !open);
      h.setAttribute("aria-expanded", open ? "true" : "false");
    }
    function toggle() { set(box.classList.contains("is-closed")); syncAll(); }
    h.addEventListener("click", function (e) { if (!e.target.closest("a")) toggle(); });
    h.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
    });
    set(!box.classList.contains("start-closed") || !!(box.closest && box.closest(".is-filtered")));
    return { box: box, set: set, main: h.tagName === "H2" };
  });
  /* ---- letter bar: one letter group at a time, shown below the bar ---- */
  $$(".letters").forEach(function (bar) {
    var wrap = bar.nextElementSibling, links = $$("a", bar);
    if (!wrap) return;
    function show(id) {
      folds.forEach(function (f) {
        if (wrap.contains(f.box) && f.box.classList.contains("start-closed")) f.set(f.box.id === id);
      });
      links.forEach(function (a) {
        if (id && a.getAttribute("href") === "#" + id) a.setAttribute("aria-current", "true");
        else a.removeAttribute("aria-current");
      });
    }
    links.forEach(function (a) {
      a.setAttribute("role", "button");
      a.addEventListener("click", function (e) {
        e.preventDefault();
        show(a.hasAttribute("aria-current") ? null : a.getAttribute("href").slice(1));
      });
    });
    /* the first letter is open from the start, and again when a filter is cleared */
    function first() { if (links.length) show(links[0].getAttribute("href").slice(1)); }
    if (!wrap.classList.contains("is-filtered")) first();
    wrap.addEventListener("oj-filter", function (e) { if (!e.detail) first(); });
  });
  var allBtn = null;
  function syncAll() {
    if (!allBtn) return;
    var anyOpen = folds.some(function (f) { return f.main && !f.box.classList.contains("is-closed"); });
    allBtn.textContent = anyOpen ? T.fold_all : T.unfold_all;
    allBtn.setAttribute("data-open", anyOpen ? "1" : "0");
  }
  if (folds.filter(function (f) { return f.main; }).length > 1) {
    var body = $(".page-body");
    allBtn = el("button", "fold-all");
    allBtn.type = "button";
    allBtn.addEventListener("click", function () {
      var close = allBtn.getAttribute("data-open") === "1";
      folds.forEach(function (f) { if (f.main) f.set(!close); });
      syncAll();
    });
    body.insertBefore(allBtn, body.firstChild);
    syncAll();
  }
  function openHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id) return;
    var t = doc.getElementById(id);
    if (!t) return;
    tabsets.forEach(function (s) {
      s.panels.forEach(function (p, i) { if (p === t || p.contains(t)) s.show(i, false); });
    });
    var isTab = false;
    if (secTabs) secTabs.secs.forEach(function (x, i) {
      if (x === t || x.contains(t)) { secTabs.show(i, false); isTab = x === t; }
    });
    folds.forEach(function (f) { if (f.box === t || f.box.contains(t)) f.set(true); });
    for (var d = t; d && d !== doc.body; d = d.parentNode) if (d.tagName === "DETAILS") d.open = true;
    syncAll();
    if (t.scrollIntoView && !isTab) t.scrollIntoView();
  }
  openHash();
  window.addEventListener("hashchange", openHash);

  /* ---- outline: mark the section in view ---- */
  var outline = $(".outline");
  if (outline && "IntersectionObserver" in window) {
    var links = {}, visible = {};
    $$("a", outline).forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
    var cur = null;
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { visible[e.target.id] = e.isIntersecting; });
      var first = null;
      for (var id in links) if (visible[id]) { first = id; break; }
      if (first && first !== cur) {
        if (cur && links[cur]) links[cur].removeAttribute("aria-current");
        links[first].setAttribute("aria-current", "true");
        cur = first;
      }
    }, { rootMargin: "-64px 0px -55% 0px" });
    for (var id in links) { var s = doc.getElementById(id); if (s) io.observe(s); }
  }
})();
