// ElderLife AI - Power Query (M) for Power BI Desktop.
// 1) Home > Transform data > Manage Parameters: create  BaseUrl (Text, e.g. "http://localhost:8000")  and  ExportKey (Text).
//    ExportKey = the backend's EXPORT_KEY (read-only, set in .env). Alternatively use a login token and change the header (see README).
// 2) Home > New Source > Blank Query > Advanced Editor: paste each query below (one per table). Names must stay lowercase: the DAX file uses them.
// NOT opened in Power BI Desktop in the authoring environment; if a type conversion fails, check the column in the data dictionary.

// ---------- helper (name it fnExport) ----------
(name as text) =>
let
    Raw = Csv.Document(Web.Contents(BaseUrl, [RelativePath = "export/" & name, Headers = [#"X-Export-Key" = ExportKey]]), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Raw, [PromoteAllScalars = true])
in
    Promoted

// ---------- alerts ----------
let
    S = fnExport("alerts"),
    T = Table.TransformColumnTypes(S, {{"id", Int64.Type}, {"elderly_id", Int64.Type}, {"stage", Int64.Type}, {"created_at", type datetime}, {"resolved_at", type datetime}}),
    Day = Table.AddColumn(T, "created_date", each DateTime.Date([created_at]), type date),
    Order = Table.AddColumn(Day, "level_order", each List.PositionOf({"Normal", "Low", "Medium", "High", "Critical"}, [level]), Int64.Type)
in
    Order

// ---------- risk ----------
let
    S = fnExport("risk"),
    T = Table.TransformColumnTypes(S, {{"elderly_id", Int64.Type}, {"score", type number}, {"created_at", type datetime}}),
    Day = Table.AddColumn(T, "created_date", each DateTime.Date([created_at]), type date),
    Order = Table.AddColumn(Day, "level_order", each List.PositionOf({"Normal", "Low", "Medium", "High", "Critical"}, [level]), Int64.Type)
in
    Order

// ---------- events ----------
let
    S = fnExport("events"),
    T = Table.TransformColumnTypes(S, {{"id", Int64.Type}, {"elderly_id", Int64.Type}, {"value", type number}, {"created_at", type datetime}}),
    Day = Table.AddColumn(T, "created_date", each DateTime.Date([created_at]), type date),
    Hour = Table.AddColumn(Day, "hour", each Time.Hour(DateTime.Time([created_at])), Int64.Type)
in
    Hour

// ---------- checkins ----------
let
    S = fnExport("checkins"),
    T = Table.TransformColumnTypes(S, {{"id", Int64.Type}, {"elderly_id", Int64.Type}, {"scheduled_at", type datetime}, {"responded_at", type datetime}}),
    Day = Table.AddColumn(T, "scheduled_date", each DateTime.Date([scheduled_at]), type date)
in
    Day

// ---------- careplan ----------
let
    S = fnExport("careplan"),
    T = Table.TransformColumnTypes(S, {{"id", Int64.Type}, {"elderly_id", Int64.Type}})
in
    T

// ---------- people ----------
let
    S = fnExport("people"),
    T = Table.TransformColumnTypes(S, {{"elderly_id", Int64.Type}, {"age", Int64.Type}, {"baseline_activity", type number}, {"caregiver_id", Int64.Type}}),
    Band = Table.AddColumn(T, "age_band", each if [age] = null then "unknown" else if [age] < 70 then "<70" else if [age] < 80 then "70-79" else if [age] < 90 then "80-89" else "90+", type text)
in
    Band
