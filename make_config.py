import json
res = json.load(open("probe_results.json"))
pick = {  # employer -> (system, slug): the live board with the most postings
 "Stripe":("greenhouse","stripe"),"Robinhood":("greenhouse","robinhood"),"Coinbase":("greenhouse","coinbase"),
 "SoFi":("greenhouse","sofi"),"Affirm":("greenhouse","affirm"),"Chime":("greenhouse","chime"),
 "Brex":("greenhouse","brex"),"Toast":("greenhouse","toast"),"Plaid":("ashby","plaid"),"Ramp":("ashby","ramp"),
 "Mercury":("greenhouse","mercury"),"Block":("greenhouse","block"),"Carta":("greenhouse","carta"),
 "Gusto":("greenhouse","gusto"),"Betterment":("greenhouse","betterment"),"Upstart":("greenhouse","upstart"),
 "Adyen":("greenhouse","adyen"),"Bill.com":("greenhouse","billcom"),"Airwallex":("ashby","airwallex"),
 "Monzo":("greenhouse","monzo"),"Payoneer":("greenhouse","payoneer"),"Jane Street":("greenhouse","janestreet"),
 "Point72":("greenhouse","point72"),"Ripple":("greenhouse","ripple"),"Wealthfront":("lever","wealthfront"),
 "Anchorage":("lever","anchorage"),"Nubank":("ashby","nubank"),
}
by = {(r["employer"],r["system"],r["slug"]):r for r in res}
out=[]
for e,(sy,sl) in pick.items():
    r=by[(e,sy,sl)]; assert r["status"]==200 and r["count"]>0, e
    out.append({"name":e,"system":sy,"slug":sl,"url":r["url"],"postings_at_test":r["count"]})
json.dump({"tested":"2026-11-16","sources":out},open("sources.json","w"),indent=1)
print(len(out))
