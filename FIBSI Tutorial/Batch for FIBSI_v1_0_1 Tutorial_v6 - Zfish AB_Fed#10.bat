FIBSI_v1_0_1.py ZfishTutorial_AB_Fed#10.csv -o ZfishTutorial_AB_Fed#10_Retrograde -c 2 1 -r 0 1A 2A 3A 4A 5A 6A 7A 20A --rdiv 20A --norm rmd,50 --evts dfy xc,3 yc,0,0 --renorm above --reevts dfy xc,3 yc,0,0 -p --plot raw fity dfy evts save_csv save_png,200

FIBSI_v1_0_1_calcium.py ZfishTutorial_AB_Fed#10.csv -o ZfishTutorial_AB_Fed#10_Anterograde -c 2 1 -r 0 8A 9A 10A 11A 12A 13A 14A 15A 16A 17A 18A 19A 20A --rdiv 20A --norm rmd,25 --evts dfy xc,3 yc,0,0 --renorm below --reevts dfy xc,3 yc,0,0 -p --plot raw fity dfy evts save_csv save_png,200

FIBSI_v1_0_1.py ZfishTutorial_AB_Fed#10.csv -o ZfishTutorial_AB_Fed#10_Anus -c 2 1 -r 0 17A 18A 19A 20A --rdiv 20A --norm rmd,10 --evts dfy xc,1 yc,0,0 --renorm above --reevts dfy xc,3 yc,0,0 -p --plot raw fity dfy evts save_csv save_png,200