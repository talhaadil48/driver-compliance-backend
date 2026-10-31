import csv
import io

raw_csv = """NameHtml,Safeguarding Expiry Date,DBS Update Expiry,Latest Card,Card Type,Driver callsign
Emre Acun,2027-10-14,2027-02-07,15618314183,Driver,245
Mohammad Afzal,,,,None,30
Saman Ahmad,2027-05-15,2027-06-27,18356382411,Driver,305
Ali Ahmed,2028-10-08,2027-02-10,17688162134,Driver,396
Gulfam Ahmed,2027-08-05,2027-03-30,17753303011,Driver,206
Ibrar Ahmed,2028-07-14,2027-01-13,19093553371,Driver,10
Sheraz Ashraf,2027-08-27,2027-10-06,17529883023,Driver,310
Halil Aytemir,,,,None,252
Nadia Azam,2029-07-22,2027-09-08,18465545274,Passenger,
Suddaf Begum,2027-08-02,2027-04-30,17336573614,Passenger,
Zenab Begum,2027-08-01,2027-08-12,17463180303,Driver,200
Gagan Bembi,,,,None,610
Muhammad Binyamin,,,,None,
Muhammad Cheema,,,,None,624
Georgi Chernev,2028-04-10,2027-07-11,18864964923,Driver,
Silvia Cherneva,2028-06-03,2026-12-27,19080390703,Driver,242
Loraine Farley,2027-08-15,2027-10-10,16760977001,Passenger,
Waqar Ghazanfar Begum,,,,None,
Mudasar Hafeez,2028-05-14,2027-06-09,17843230523,Driver,307
Asif Hussain,2027-09-11,2027-02-05,19124287931,Driver,104
Farrukh Hussain,2027-06-07,2027-01-14,16437703074,Driver,364
Mohammad Iqbal,2029-07-22,2027-02-17,16906613585,Driver,3
Raees Iqbal,2029-05-18,2027-10-17,19447632481,Driver,393
Liaquat Javed,2026-10-17,2027-06-18,18832704311,Driver,1
Majid Jehangir,2028-01-29,2027-03-15,18715208442,Driver,394
Baljeet Jossan,,,,None,614
Shorish Karim,2027-05-14,2027-05-04,16142144614,Driver,225
Irfan Khaliq,2029-01-29,2027-10-29,19462011701,Driver,117
Shakeel Mahmood,2028-06-16,2027-06-04,19268733851,Driver,226
Tariq Mahmood,2028-07-10,2027-05-01,18769739812,Driver,337/515
Mohammad Majid,2027-09-10,2027-06-04,16175196224,Driver,107
Shoaib Mukhtar,2027-12-12,2026-12-12,16847358534,Driver,356
Waheed Mushtaq,2027-10-22,2027-10-12,17127509514,Driver,315
Muhammad Nadeem,2027-07-31,2027-06-23,17016863512,Driver,301
Aqib Nadeem Rashid,2028-02-15,2027-03-12,19170099292,Driver,217
Amjad Naveed,2029-01-16,2027-05-16,17812253953,Driver,348
Faisal Naveed Mehr,2028-07-30,2027-01-30,19569686641,Driver,212
Imran Nazir,,,,None,603
Imran Rafiq Akhtar,2028-01-28,2026-11-30,16825406654,Driver,359
Mohammed Rahim,2027-11-18,2027-10-28,15505252024,Driver,309
Arshed Ratyal,2027-06-03,2027-01-05,16006851674,Driver,352
Obaid Rauf,2028-06-19,2027-03-29,16530394165,Driver,303
Azhar Sadiq,2029-01-14,2027-04-20,16968173714,Driver,116
Abdul Sattar,2027-08-02,2027-08-12,19817535691,Driver,22
Mohammed Shafiq,2027-08-14,2027-03-19,16516610634,Driver,316
Muhammad Shahzad,2028-02-02,2027-10-12,16335031415,Driver,442
Valdis Sleiers,2027-08-14,2027-08-18,17469220673,Driver,371
Zain Talib,2028-06-30,2027-09-10,19394779881,Driver,343
Haroon Tariq,2028-07-10,2026-11-14,18063014013,Driver,
Nazish Tariq,2027-06-18,2026-12-14,18601866571,Driver,330
Zumar Tariq,2027-07-22,2027-06-14,18827596583,Driver,320
Angela Topliss,2027-08-16,2027-08-07,18901632932,Passenger,
Muhammad Wasim,2029-05-18,2026-12-08,18104226013,Driver,110
Muhammad Younas,2028-07-23,2027-03-27,15677899711,Driver,7
Mohammad Yousaf,2029-08-28,2026-11-12,17164757314,Driver,9"""

reader = csv.DictReader(io.StringIO(raw_csv.strip()))
valid_drivers = []
missing_id_drivers = []

for row in reader:
    name = row["NameHtml"].strip()
    sg_exp = row["Safeguarding Expiry Date"].strip() or None
    dbs_exp = row["DBS Update Expiry"].strip() or None
    card = row["Latest Card"].strip() or None
    card_type = row["Card Type"].strip() or None
    callsign_raw = row["Driver callsign"].strip()

    if not callsign_raw:
        missing_id_drivers.append({
            "name": name,
            "safeguarding_expiry": sg_exp,
            "dbs_expiry": dbs_exp,
            "card": card,
            "card_type": card_type
        })
    else:
        # Check if callsign has 2 ids (e.g. 337/515)
        if "/" in callsign_raw:
            callsign = callsign_raw.split("/")[0].strip()
            print(f"Driver {name} had multiple IDs ({callsign_raw}), picked {callsign}")
        elif "," in callsign_raw:
            callsign = callsign_raw.split(",")[0].strip()
        else:
            callsign = callsign_raw

        valid_drivers.append({
            "name": name,
            "callsign": callsign,
            "raw_callsign": callsign_raw,
            "safeguarding_expiry": sg_exp,
            "dbs_expiry": dbs_exp,
            "card": card,
            "card_type": card_type
        })

print(f"Total Rows: {len(valid_drivers) + len(missing_id_drivers)}")
print(f"Valid Drivers to add: {len(valid_drivers)}")
print(f"Drivers with missing ID: {len(missing_id_drivers)}")
print("\nMissing ID List:")
for d in missing_id_drivers:
    print(f" - {d['name']} (Card Type: {d['card_type']}, Card: {d['card']})")
