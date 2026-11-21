/* Tiny, safe Markdown renderer for AI answers.
 * Escapes HTML first, then builds only the tags it knows: p, ul, ol, li, strong, code, pre.
 * No links, no images, no raw HTML -> nothing from the model or from pasted pages can run. */
(function (root, factory) {
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.HamoMarkdown = factory();
    }
})(typeof self !== "undefined" ? self : this, function () {
    "use strict";

    function escapeHtml(s) {
        return s
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function inline(escaped) {
        return escaped
            .replace(/`([^`\n]+)`/g, "<code>$1</code>")
            .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    }

    function render(source) {
        var lines = String(source).replace(/\r\n?/g, "\n").split("\n");
        var out = [];
        var list = null;
        var para = [];
        var code = null;

        function flushPara() {
            if (para.length) {
                out.push("<p>" + para.map(inline).join("<br>") + "</p>");
                para = [];
            }
        }
        function closeList() {
            if (list) {
                out.push("</" + list + ">");
                list = null;
            }
        }

        for (var i = 0; i < lines.length; i++) {
            var raw = lines[i];

            if (code !== null) {
                if (/^\s*```/.test(raw)) {
                    out.push("<pre><code>" + code.join("\n") + "</code></pre>");
                    code = null;
                } else {
                    code.push(escapeHtml(raw));
                }
                continue;
            }
            if (/^\s*```/.test(raw)) {
                flushPara();
                closeList();
                code = [];
                continue;
            }

            var line = escapeHtml(raw);
            var m;

            if (!line.trim()) {
                flushPara();
                closeList();
            } else if ((m = /^\s*#{1,6}\s+(.*)$/.exec(line))) {
                flushPara();
                closeList();
                out.push('<p class="md-h">' + inline(m[1]) + "</p>");
            } else if ((m = /^\s*[-*\u2022]\s+(.*)$/.exec(line))) {
                flushPara();
                if (list !== "ul") {
                    closeList();
                    out.push("<ul>");
                    list = "ul";
                }
                out.push("<li>" + inline(m[1]) + "</li>");
            } else if ((m = /^\s*[0-9\u0660-\u0669]+[.)]\s+(.*)$/.exec(line))) {
                flushPara();
                if (list !== "ol") {
                    closeList();
                    out.push("<ol>");
                    list = "ol";
                }
                out.push("<li>" + inline(m[1]) + "</li>");
            } else {
                closeList();
                para.push(line);
            }
        }

        if (code !== null) {
            out.push("<pre><code>" + code.join("\n") + "</code></pre>");
        }
        flushPara();
        closeList();
        return out.join("");
    }

    return { render: render, escapeHtml: escapeHtml };
});
