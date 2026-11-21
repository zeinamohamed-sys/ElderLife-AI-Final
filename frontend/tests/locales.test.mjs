import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import en from "../src/locales/en.js";
import ar from "../src/locales/ar.js";
const ph = (s) => (s.match(/\{\w+\}/g) || []).sort().join();
test("Arabic and English have exactly the same keys", () => {
  assert.deepEqual(Object.keys(en).filter((k) => !(k in ar)), []); assert.deepEqual(Object.keys(ar).filter((k) => !(k in en)), []);
});
test("placeholders match between languages", () => { for (const k of Object.keys(en)) if (k in ar) assert.equal(ph(en[k]), ph(ar[k]), k); });
test("no empty translations; Arabic strings contain Arabic script (except brand/units)", () => {
  for (const [k, v] of Object.entries(ar)) { assert.ok(v.trim().length > 0, k); }
  const latinOnly = Object.entries(ar).filter(([k, v]) => !/[\u0600-\u06FF]/.test(v)).map(([k]) => k);
  assert.ok(latinOnly.length <= 8, "too many untranslated Arabic strings: " + latinOnly.join(", "));
});
test("every literal t('key') used in the source exists in both dictionaries", () => {
  const files = ["App.jsx", "components.jsx", "pages.jsx", "i18n.jsx", "api.js"].map((f) => fs.readFileSync(new URL("../src/" + f, import.meta.url), "utf8"));
  const used = new Set(); for (const src of files) for (const m of src.matchAll(/\bt\("([\w.]+)"\s*[,)]/g)) used.add(m[1]); for (const m of files.join("").matchAll(/translate\(\w+, "([\w.]+)"/g)) used.add(m[1]);
  const missing = [...used].filter((k) => !(k in en) || !(k in ar)); assert.deepEqual(missing, []);
});
test("RTL is wired: provider sets dir=rtl for Arabic and the stylesheet has RTL rules", () => {
  assert.match(fs.readFileSync(new URL("../src/i18n.jsx", import.meta.url), "utf8"), /dir = lang === "ar" \? "rtl" : "ltr"/);
  assert.match(fs.readFileSync(new URL("../src/styles.css", import.meta.url), "utf8"), /\[dir=rtl\]/);
});
test("keys built at run time (prefix + value) exist for every value the backend can send", () => {
  const dyn = { evt: ["activity", "fall", "ok", "sos"], level: ["Normal", "Low", "Medium", "High", "Critical"], kind: ["medication", "meal", "water", "activity"],
    status: ["open", "acknowledged", "resolved"], by: ["person", "caregiver"], role: ["admin", "caregiver"], "ov.status": ["ok", "attention", "critical"], "ov.anom": ["activity_drop", "missed_checkin"], "ci.status": ["answered", "missed", "pending"] };
  for (const [p, vs] of Object.entries(dyn)) for (const v of vs) { assert.ok(`${p}.${v}` in en, `en ${p}.${v}`); assert.ok(`${p}.${v}` in ar, `ar ${p}.${v}`); }
});
