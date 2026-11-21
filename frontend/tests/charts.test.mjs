import test from "node:test";
import assert from "node:assert/strict";
import { barHeights, countByLevel, levelIndex, seriesPoints, trendPoints } from "../src/lib/charts.js";
test("levelIndex orders the levels and treats unknown as Normal", () => { assert.equal(levelIndex("Critical"), 4); assert.equal(levelIndex("Normal"), 0); assert.equal(levelIndex("???"), 0); });
test("trendPoints goes oldest -> newest, Critical at the top", () => {
  const p = trendPoints([{ level: "Critical" }, { level: "Normal" }], 100, 40, 0);   // API order: newest first
  assert.deepEqual(p, [[0, 40], [100, 0]]);
  assert.deepEqual(trendPoints([]), []); assert.equal(trendPoints([{ level: "Low" }]).length, 1);
});
test("barHeights scales to the tallest bar and survives zeros / bad numbers", () => {
  assert.deepEqual(barHeights([0, 5, 10], 100), [0, 50, 100]); assert.deepEqual(barHeights([0, 0]), [0, 0]); assert.deepEqual(barHeights([null, "x", 2], 10), [0, 0, 10]);
});
test("countByLevel", () => { assert.deepEqual(countByLevel([{ level: "High" }, { level: "High" }, { level: "Low" }]), [0, 1, 0, 2, 0]); assert.deepEqual(countByLevel(undefined), [0, 0, 0, 0, 0]); });
test("seriesPoints splits at gaps and scales to the max", () => {
  const { segments, max } = seriesPoints([10, 20, null, 5], 100, 50, 0); assert.equal(max, 20); assert.equal(segments.length, 2); assert.deepEqual(segments[0], [[0, 25], [33.3, 0]]); assert.equal(segments[1].length, 1);
  assert.deepEqual(seriesPoints([null, null]).segments, []); assert.equal(seriesPoints([0, 0]).max, 1);
});
