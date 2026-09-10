import frappe

DRY_RUN = False
DATA = [
    {"item_code": "366124371", "part_no": "B7277-EG01A"},
    {"item_code": "SPR002705", "part_no": "B7277-EG01A"},
    {"item_code": "C241-1HS0A", "part_no": "C9241-1HS0A"},
    {"item_code": "SPR001204", "part_no": "C9241-1HS0A"},
    {"item_code": "C9GDAED00K", "part_no": "C9GDA-ED00K"},
    {"item_code": "SPR000208", "part_no": "C9GDA-ED00K"},
    {"item_code": "355015981", "part_no": "D1060-1HA1A"},
    {"item_code": "SPR003672", "part_no": "D1060-1HA1A"},
    {"item_code": "355020401", "part_no": "D4060-3JY0B"},
    {"item_code": "SPR000220", "part_no": "D4060-3JY0B"},
    {"item_code": "366101251", "part_no": "FL400S"},
    {"item_code": "SPR002430", "part_no": "FL400S"},
    {"item_code": "366101811", "part_no": "G1016056847"},
    {"item_code": "G1016056847", "part_no": "G1016056847"},
    {"item_code": "G101605770551", "part_no": "G101605770551"},
    {"item_code": "SPR006985", "part_no": "G101605770551"},
    {"item_code": "742901051", "part_no": "G1017041361"},
    {"item_code": "G1017041361", "part_no": "G1017041361"},
    {"item_code": "G1056005000", "part_no": "G1056005000"},
    {"item_code": "SPR001644", "part_no": "G1056005000"},
    {"item_code": "366100511", "part_no": "G1056025900"},
    {"item_code": "G1056025900", "part_no": "G1056025900"},
    {"item_code": "G1136000118", "part_no": "G1136000118"},
    {"item_code": "SPR002282", "part_no": "G1136000118"},
    {"item_code": "366132191", "part_no": "G2032047000"},
    {"item_code": "G2032047000", "part_no": "G2032047000"},
    {"item_code": "SPR003740", "part_no": "G2032047000"},
    {"item_code": "G2032058300", "part_no": "G2032058300"},
    {"item_code": "SPR003747", "part_no": "G2032058300"},
    {"item_code": "G2032061800", "part_no": "G2032061800"},
    {"item_code": "GS6608445268", "part_no": "G2032061800"},
    {"item_code": "SPR003749", "part_no": "G2032061800"},
    {"item_code": "G2032074200", "part_no": "G2032074200"},
    {"item_code": "SPR003743", "part_no": "G2032074200"},
    {"item_code": "G2036014400", "part_no": "G2036014400"},
    {"item_code": "SPR003742", "part_no": "G2036014400"},
    {"item_code": "G5049026500", "part_no": "G5049026500"},
    {"item_code": "SPR007038", "part_no": "G5049026500"},
    {"item_code": "G5068004400", "part_no": "G5068004400"},
    {"item_code": "SPR007023", "part_no": "G5068004400"},
    {"item_code": "G5081039000", "part_no": "G5081039000"},
    {"item_code": "SPR002995", "part_no": "G5081039000"},
    {"item_code": "6044150000", "part_no": "G6044150000"},
    {"item_code": "SPR007022", "part_no": "G6044150000"},
    {"item_code": "G6608101372", "part_no": "G6608101372"},
    {"item_code": "SPR003773", "part_no": "G6608101372"},
    {"item_code": "366124221", "part_no": "G8025530200"},
    {"item_code": "G8025530200", "part_no": "G8025530200"},
    {"item_code": "G8025530400", "part_no": "G8025530400"},
    {"item_code": "SPR003752", "part_no": "G8025530400"},
    {"item_code": "G8025530500", "part_no": "G8025530500"},
    {"item_code": "SPR003750", "part_no": "G8025530500"},
    {"item_code": "366122101", "part_no": "G8025530600"},
    {"item_code": "G8025530600", "part_no": "G8025530600"},
    {"item_code": "GS6608445069", "part_no": "G8025530600"},
    {"item_code": "G9020009300", "part_no": "G9020009300"},
    {"item_code": "LUB000195", "part_no": "G9020009300"},
    {"item_code": "KLE24-TKA04", "part_no": "KLE24-TKA04"},
    {"item_code": "KLE5300004", "part_no": "KLE53-00004"},
    {"item_code": "LUB000118", "part_no": "KLE53-00004"},
    {"item_code": "366101511", "part_no": "LR073669"},
    {"item_code": "LR073669", "part_no": "LR073669"},
    {"item_code": "LR133455", "part_no": "LR133455"},
    {"item_code": "SPR002309", "part_no": "LR133455"},
    {"item_code": "MD136466", "part_no": "MD136466"},
    {"item_code": "SMD136466V", "part_no": "MD136466"},
    {"item_code": "SPR001478", "part_no": "ME130968"},
    {"item_code": "SPR003571", "part_no": "ME130968"},
    {"item_code": "SPR000074", "part_no": "ME227821"},
    {"item_code": "SPR001000", "part_no": "ME227821"},
    {"item_code": "SPR003564", "part_no": "ME227821"},
    {"item_code": "SPR001480", "part_no": "ME294400"},
    {"item_code": "SPR005513", "part_no": "ME294400"},
    {"item_code": "SPR000285", "part_no": "MK666976"},
    {"item_code": "SPR006431", "part_no": "MK666976"},
    {"item_code": "SPR000146", "part_no": "MZ690150"},
    {"item_code": "SPR000492", "part_no": "MZ690150"},
    {"item_code": "SPR005246", "part_no": "MZ690193"},
    {"item_code": "SPR005472", "part_no": "MZ690193"},
    {"item_code": "366100281", "part_no": "MZ691140"},
    {"item_code": "SPR001739", "part_no": "MZ691140"},
    {"item_code": "SPR005979", "part_no": "OSRAM-APO2825"},
    {"item_code": "SPR005987", "part_no": "OSRAM-APO7506"},
    {"item_code": "SPR005986", "part_no": "OSRAM-APO7507"},
    {"item_code": "366100611", "part_no": "04152-37010"},
    {"item_code": "SPR005248", "part_no": "04152-37010"},
    {"item_code": "366100731", "part_no": "04152-38010"},
    {"item_code": "SPR003209", "part_no": "04152-38010"},
    {"item_code": "SPR005480", "part_no": "04152-38010"},
    {"item_code": "SPR000716", "part_no": "04152-38020"},
    {"item_code": "SPR000835", "part_no": "04152-38020"},
    {"item_code": "SPR005506", "part_no": "04152-38020"},
    {"item_code": "04465-0K580", "part_no": "04465-0K580"},
    {"item_code": "355014121", "part_no": "04465-0K580"},
    {"item_code": "355015831", "part_no": "04465-26421"},
    {"item_code": "SPR003520", "part_no": "04465-26421"},
    {"item_code": "355013151", "part_no": "04465-60280"},
    {"item_code": "SPR000690", "part_no": "04465-60280"},
    {"item_code": "04466-26030", "part_no": "04466-26030"},
    {"item_code": "355040131", "part_no": "04466-26030"},
    {"item_code": "SPR000494", "part_no": "06E115562C"},
    {"item_code": "SPR003277", "part_no": "06E115562C"},
    {"item_code": "358288021", "part_no": "08823-80250"},
    {"item_code": "LUB000170", "part_no": "08823-80250"},
    {"item_code": "LUB000019", "part_no": "08886-81885"},
    {"item_code": "LUB000070", "part_no": "08886-81885"},
    {"item_code": "LUB000125", "part_no": "08886-81895"},
    {"item_code": "LUB000165", "part_no": "08886-81895"},
    {"item_code": "366101781", "part_no": "100180"},
    {"item_code": "SPR005036", "part_no": "100180"},
    {"item_code": "11026-JA00A", "part_no": "11026-01M02"},
    {"item_code": "SPR004180", "part_no": "11026-01M02"},
    {"item_code": "SPR007215", "part_no": "1109.AY"},
    {"item_code": "1109AL", "part_no": "1109AL"},
    {"item_code": "366100111", "part_no": "1109AL"},
    {"item_code": "366102701", "part_no": "11427953125"},
    {"item_code": "SPR000133", "part_no": "12605566"},
    {"item_code": "SPR001058", "part_no": "12605566"},
    {"item_code": "12611384", "part_no": "12611384"},
    {"item_code": "SPR000727", "part_no": "12611384"},
    {"item_code": "12625298", "part_no": "12625298"},
    {"item_code": "SPR002691", "part_no": "12625298"},
    {"item_code": "12637187", "part_no": "12637187"},
    {"item_code": "SPR001578", "part_no": "12637187"},
    {"item_code": "12757188", "part_no": "12657188"},
    {"item_code": "1269-6434", "part_no": "12696434"},
    {"item_code": "12696434", "part_no": "12696434"},
    {"item_code": "13227300", "part_no": "13227300"},
    {"item_code": "SPR000389", "part_no": "13227300"},
    {"item_code": "1327-1583", "part_no": "13271583"},
    {"item_code": "SPR001159", "part_no": "13271583"},
    {"item_code": "SPR001471", "part_no": "13465094"},
    {"item_code": "SPR005617", "part_no": "13465094"},
    {"item_code": "1505433-00-C", "part_no": "1505433-00-C"},
    {"item_code": "1505433-00-C-U", "part_no": "1505433-00-C"},
    {"item_code": "15077362", "part_no": "15077362"},
    {"item_code": "SPR001385", "part_no": "15077362"},
    {"item_code": "366100171", "part_no": "15208-1HC0A"},
    {"item_code": "SPR004763", "part_no": "15208-1HC0A"},
    {"item_code": "SPR001349", "part_no": "15208-31U0B"},
    {"item_code": "SPR005043", "part_no": "15208-31U0B"},
    {"item_code": "366101041", "part_no": "15601-BZ010"},
    {"item_code": "SPR000317", "part_no": "15601-BZ010"},
    {"item_code": "16546-6CA0A", "part_no": "16546-6CA0A"},
    {"item_code": "165466CA0A", "part_no": "16546-6CA0A"},
    {"item_code": "SPR003573", "part_no": "16546-6CA0B"},
    {"item_code": "SPR005477", "part_no": "16546-6CA0B"},
    {"item_code": "366130951", "part_no": "16546-ED500"},
    {"item_code": "SPR000043", "part_no": "16546-ED500"},
    {"item_code": "SPR003671", "part_no": "16546-ED500"},
    {"item_code": "366130351", "part_no": "16546-JG30A"},
    {"item_code": "SPR000848", "part_no": "16546-JG30A"},
    {"item_code": "SPR000906", "part_no": "16546-JG30A"},
    {"item_code": "SPR005478", "part_no": "16546-JG30A"},
    {"item_code": "366133861", "part_no": "17801-0C010"},
    {"item_code": "SPR005698", "part_no": "17801-0C010"},
    {"item_code": "366132411", "part_no": "17801-0L040"},
    {"item_code": "SPR001032", "part_no": "17801-0L040"},
    {"item_code": "SPR003343", "part_no": "17801-0L040"},
    {"item_code": "SPR000519", "part_no": "17801-21050"},
    {"item_code": "SPR001972", "part_no": "17801-21050"},
    {"item_code": "366136401", "part_no": "17801-38030"},
    {"item_code": "SPR001310", "part_no": "17801-38030"},
    {"item_code": "17801-62010", "part_no": "17801-62010"},
    {"item_code": "1780162010", "part_no": "17801-62010"},
    {"item_code": "17801-BZ130-AM", "part_no": "17801-BZ130"},
    {"item_code": "SPR006418", "part_no": "17801-BZ130"},
    {"item_code": "366132851", "part_no": "17801-BZ150"},
    {"item_code": "SPR005939", "part_no": "17801-BZ150"},
    {"item_code": "1920-8675", "part_no": "19208675"},
    {"item_code": "SPR001389", "part_no": "19208675"},
    {"item_code": "LUB000015", "part_no": "19347199"},
    {"item_code": "SPR001472", "part_no": "19347199"},
    {"item_code": "LUB000030", "part_no": "19433495"},
    {"item_code": "LUB000126", "part_no": "19433495"},
    {"item_code": "SPR002204", "part_no": "21430-C993B"},
    {"item_code": "SPR006648", "part_no": "21430-C993B"},
    {"item_code": "SPR001454", "part_no": "22401-1HC1B"},
    {"item_code": "SPR003824", "part_no": "22401-1HC1B"},
    {"item_code": "SPR000576", "part_no": "22845992"},
    {"item_code": "SPR000862", "part_no": "22845992"},
    {"item_code": "24280048", "part_no": "24280048"},
    {"item_code": "SPR000791", "part_no": "24280048"},
    {"item_code": "SPR001267", "part_no": "25195785"},
    {"item_code": "SPR001600", "part_no": "25195785"},
    {"item_code": "25798013", "part_no": "25798013"},
    {"item_code": "SPR001602", "part_no": "25798013"},
    {"item_code": "SPR001331", "part_no": "26320-3C100"},
    {"item_code": "SPR005467", "part_no": "26320-3C100"},
    {"item_code": "26320-3CAA0", "part_no": "26320-3CAA0"},
    {"item_code": "263203CAA0", "part_no": "26320-3CAA0"},
    {"item_code": "SPR002872", "part_no": "26320-3CAA0"},
    {"item_code": "SPR001281", "part_no": "26350 2J000"},
    {"item_code": "SPR003538", "part_no": "26350 2J000"},
    {"item_code": "26350-2M000", "part_no": "26350-2M000"},
    {"item_code": "SPR000699", "part_no": "26350-2M000"},
    {"item_code": "SPR000082", "part_no": "26350-2S001"},
    {"item_code": "SPR005291", "part_no": "26350-2S001"},
    {"item_code": "366120971", "part_no": "27277-1HDKE"},
    {"item_code": "SPR001311", "part_no": "27277-1HDKE"},
    {"item_code": "SPR003586", "part_no": "27277-1HDKE"},
    {"item_code": "27277-4EM0A", "part_no": "27277-4EM0A"},
    {"item_code": "SPR005533", "part_no": "27277-4EM0A"},
    {"item_code": "27277-9NM0A", "part_no": "27277-9NM0A"},
    {"item_code": "SPR000320", "part_no": "27277-9NM0A"},
    {"item_code": "SPR004295", "part_no": "27891-3YF1A"},
    {"item_code": "SPR006676", "part_no": "27891-3YF1A"},
    {"item_code": "28113-C7000", "part_no": "28113-C7000"},
    {"item_code": "SPR003583", "part_no": "28113-C7000"},
    {"item_code": "288901LB0A", "part_no": "28890-1LB0A"},
    {"item_code": "SPR000111", "part_no": "28890-1LB0A"},
    {"item_code": "31397-1XJ0A", "part_no": "31397-1XJ0A"},
    {"item_code": "SPR000704", "part_no": "31397-1XJ0A"},
    {"item_code": "32140029-AM", "part_no": "32140029"},
    {"item_code": "SPR001061", "part_no": "32140029"},
    {"item_code": "3516860010", "part_no": "35168-60010"},
    {"item_code": "SPR002496", "part_no": "35168-60010"},
    {"item_code": "SPR002334", "part_no": "38342-3VX0A"},
    {"item_code": "SPR005691", "part_no": "38342-3VX0A"},
    {"item_code": "52933C1100", "part_no": "52933-C1100"},
    {"item_code": "SPR000084", "part_no": "52933-C1100"},
    {"item_code": "5311326030", "part_no": "53113-26030"},
    {"item_code": "SPR001984", "part_no": "53113-26030"},
    {"item_code": "54501-1HA7A", "part_no": "54501-1HA7A"},
    {"item_code": "SPR000051", "part_no": "54501-1HA7A"},
    {"item_code": "SPR000796", "part_no": "55594651"},
    {"item_code": "SPR001473", "part_no": "55594651"},
    {"item_code": "577242P000", "part_no": "57724-2P000"},
    {"item_code": "SPR000322", "part_no": "57724-2P000"},
    {"item_code": "SPR000881", "part_no": "5876101170"},
    {"item_code": "SPR002744", "part_no": "5876101170"},
    {"item_code": "668951ZR0A", "part_no": "66895-1ZR0A"},
    {"item_code": "SPR006650", "part_no": "66895-1ZR0A"},
    {"item_code": "68191349AC", "part_no": "68191349AC"},
    {"item_code": "SPR000069", "part_no": "68191349AC"},
    {"item_code": "6980260080", "part_no": "69802-60080"},
    {"item_code": "SPR000066", "part_no": "69802-60080"},
    {"item_code": "366123481", "part_no": "7850A002"},
    {"item_code": "SPR007423", "part_no": "7850A002"},
    {"item_code": "SPR000079", "part_no": "80292-SDA-407"},
    {"item_code": "SPR005512", "part_no": "80292-SDA-407"},
    {"item_code": "SPR000199", "part_no": "84176464"},
    {"item_code": "SPR003282", "part_no": "84176464"},
    {"item_code": "SPR000594", "part_no": "84459867"},
    {"item_code": "SPR000737", "part_no": "84459867"},
    {"item_code": "SPR006726", "part_no": "848111650961"},
    {"item_code": "86793555", "part_no": "86793555"},
    {"item_code": "89793555", "part_no": "86793555"},
    {"item_code": "366120051", "part_no": "87139-52040"},
    {"item_code": "SPR004351", "part_no": "87139-52040"},
    {"item_code": "87139-YZZ25", "part_no": "87139-YZZ25"},
    {"item_code": "SPR000443", "part_no": "87139-YZZ25"},
    {"item_code": "366122311", "part_no": "88568-BZ060"},
    {"item_code": "SPR006875", "part_no": "88568-BZ060"},
    {"item_code": "LUB000016", "part_no": "88862645"},
    {"item_code": "LUB000188", "part_no": "88862645"},
    {"item_code": "8901-7872", "part_no": "89017872"},
    {"item_code": "SPR000995", "part_no": "89017872"},
    {"item_code": "6841241", "part_no": "8GA006841-241"},
    {"item_code": "8GA006841-241", "part_no": "8GA006841-241"},
    {"item_code": "178560011", "part_no": "8GA178560-011"},
    {"item_code": "8GA178560-011", "part_no": "8GA178560-011"},
    {"item_code": "178560021", "part_no": "8GA178560-021"},
    {"item_code": "8GA178560-021", "part_no": "8GA178560-021"},
    {"item_code": "178560101", "part_no": "8GA178560-101"},
    {"item_code": "8GA178560-101", "part_no": "8GA178560-101"},
    {"item_code": "178560111", "part_no": "8GD178560-111"},
    {"item_code": "SPR001083", "part_no": "8GD178560-111"},
    {"item_code": "178560341", "part_no": "8GD178560-341"},
    {"item_code": "8GD178560-341", "part_no": "8GD178560-341"},
    {"item_code": "9319001", "part_no": "8GH009319-001"},
    {"item_code": "8GH009319-001", "part_no": "8GH009319-001"},
    {"item_code": "178555011", "part_no": "8GH178555-011"},
    {"item_code": "8GH178555-011", "part_no": "8GH178555-011"},
    {"item_code": "178555081", "part_no": "8GH178555-081"},
    {"item_code": "8GH178555-081", "part_no": "8GH178555-081"},
    {"item_code": "178560271", "part_no": "8GP178560-271"},
    {"item_code": "8GP178560-271", "part_no": "8GP178560-271"},
]


def execute():
    frappe.enqueue(run_merge, queue="long", timeout=8 * 60 * 60)
    print("enqueued run_merge on long queue (timeout 8h)")


def run_merge():
    groups = {}
    for row in DATA:
        groups.setdefault(str(row["part_no"]).strip(), []).append(
            str(row["item_code"]).strip()
        )
    plan = []
    bad = []
    done = []
    for part_no, codes in groups.items():
        exists = frappe.db.exists("Item", part_no)
        present = []
        gone = []
        for c in codes:
            if frappe.db.exists("Item", c):
                present.append(c)
            else:
                gone.append(c)
        if gone and not exists:
            bad.append(part_no + ": item not found: " + ", ".join(gone))
        survivor = part_no if exists else (present[0] if present else None)
        to_merge = []
        for c in present:
            if c != survivor:
                to_merge.append(c)
        if survivor and not to_merge and exists:
            done.append(
                part_no
                + ": already done ("
                + str(len(gone))
                + " source item(s) already merged)"
            )
        for code in to_merge if survivor else []:
            src = frappe.get_doc("Item", code)
            fields = src.get_cant_change_fields()
            tgt = frappe.db.get_value("Item", survivor, fields, as_dict=True)
            for f in fields:
                a = str(src.get(f) or "")
                b = str(tgt.get(f) or "")
                if a != b:
                    bad.append(
                        part_no
                        + ": "
                        + code
                        + " vs "
                        + survivor
                        + " -> "
                        + f
                        + ": "
                        + a
                        + " != "
                        + b
                    )
        if survivor and (to_merge or not exists):
            plan.append([part_no, exists, survivor, to_merge])
    print("--- checked " + str(len(groups)) + " part numbers ---")
    for line in done:
        print("OK      " + line)
    for line in bad:
        print("BAD     " + line)
    if bad:
        print("ABORTED: " + str(len(bad)) + " problem(s) found, nothing was changed")
    errors = []
    for part_no, exists, survivor, to_merge in plan if not bad else []:
        if DRY_RUN:
            print(
                "[dry]   "
                + ("target exists " if exists else "rename " + survivor + " -> ")
                + part_no
                + "; merge "
                + str(to_merge)
            )
            continue
        try:
            if not exists:
                frappe.rename_doc("Item", survivor, part_no)
                print("renamed " + survivor + " -> " + part_no)
            for code in to_merge:
                frappe.rename_doc("Item", code, part_no, merge=True)
                print("merged  " + code + " -> " + part_no)
            frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            errors.append(part_no + ": " + str(e))
            print("FAILED  " + part_no + ": " + str(e))
    for line in errors:
        print("ERROR   " + line)
    print(
        "=== finished: "
        + str(len(plan))
        + " to do, "
        + str(len(done))
        + " already done, "
        + str(len(bad))
        + " bad, "
        + str(len(errors))
        + " errors ==="
    )
