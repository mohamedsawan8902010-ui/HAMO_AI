const assert = require("assert");
const md = require("../frontend/markdown.js");

const r = (s) => md.render(s);

// escaping: nothing from the model can become a tag
assert.strictEqual(r("<script>alert(1)</script>"), "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>");
assert.ok(!r('<img src=x onerror="alert(1)">').includes("<img"));
assert.ok(!r("[click](javascript:alert(1))").includes("<a"));
assert.ok(!r("**<b>x</b>**").includes("<b>"));

// inline
assert.strictEqual(r("هذا **مهم** جدًا"), "<p>هذا <strong>مهم</strong> جدًا</p>");
assert.strictEqual(r("استخدم `print()` هنا"), "<p>استخدم <code>print()</code> هنا</p>");

// paragraphs and line breaks
assert.strictEqual(r("سطر 1\nسطر 2\n\nفقرة"), "<p>سطر 1<br>سطر 2</p><p>فقرة</p>");

// lists (bullets, numbers, Arabic-Indic numbers) and the bold-at-line-start case
assert.strictEqual(r("- أ\n- ب"), "<ul><li>أ</li><li>ب</li></ul>");
assert.strictEqual(r("* **كلمة**: معنى"), "<ul><li><strong>كلمة</strong>: معنى</li></ul>");
assert.strictEqual(r("1. أول\n2. ثاني"), "<ol><li>أول</li><li>ثاني</li></ol>");
assert.strictEqual(r("١. أول\n٢) ثاني"), "<ol><li>أول</li><li>ثاني</li></ol>");
assert.strictEqual(r("**عنوان عريض**"), "<p><strong>عنوان عريض</strong></p>");
assert.strictEqual(r("قبل\n- عنصر\nبعد"), "<p>قبل</p><ul><li>عنصر</li></ul><p>بعد</p>");

// headings are flattened to a bold line (no big headings on a phone)
assert.strictEqual(r("## عنوان"), '<p class="md-h">عنوان</p>');

// code fences keep their content escaped and untouched by inline rules
assert.strictEqual(r("```\nif (a < b) {}\n**x**\n```"), "<pre><code>if (a &lt; b) {}\n**x**</code></pre>");
assert.strictEqual(r("```\nunclosed"), "<pre><code>unclosed</code></pre>");

// robustness
assert.strictEqual(r(""), "");
assert.strictEqual(r("\r\nسطر\r\n"), "<p>سطر</p>");
assert.strictEqual(r(12345), "<p>12345</p>");

console.log("markdown: all assertions passed");
