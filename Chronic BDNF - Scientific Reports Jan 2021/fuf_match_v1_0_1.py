import sys
import os
import argparse
import numpy as np

class Evt(object):
    def __init__(self,list):
        #roi,quad,dir,startx,endx,ampx,dur,ampy,midx,halfdur,auc
        self.roi    = list[0]
        self.quad   = list[1]
        self.dir    = list[2]
        self.startx = list[3]
        self.endx   = list[4]
        self.ampx   = list[5]
        self.dur    = list[6]
        self.ampy   = list[7]
        self.midx   = list[8]
        self.halfdur= list[9]
        self.auc    = list[10]
    def __str__(self):
        s="\t"
        s+= str(self.dir)
        s+="\t"
        s+= str(self.startx)
        s+="\t"
        s+= str(self.endx)
        s+="\t"
        s+= str(self.ampx)
        s+="\t"
        s+= str(self.ampy)
        s+="\n"
        return(s)

def e_open(filename,uffn,ffn):
    # Name file
    if ARGS.o == None: filename= str(uffn + '_' + str(ffn) + '_selected_evts.txt')
    F = open(filename,"w")
    # Write out headers
    F.write("\t\t\t\t\t\t\t\t"+str(uffn)+"\t"+str(ffn)+"\t"+filename+"\n")
    F.write("ROI(orig)\tQuadrant(orig)\tDirection\tStart time (s)\tEnd time (s)\tPeak time (s)\tDuration (s)\tAmplitude\tMidpoint (s)\tHalf Duration(s)\tAUC\n")
    return(F,filename)

def e_close(F,filename):
    F.close()
    print(filename)
    
def e_out(F,selectedUFevts, filename,uffn,ffn):
    for evt in selectedUFevts:
        s = evt.roi + "\t" + str(evt.quad)+ "\t" + str(evt.dir) + "\t" + str(evt.startx) + "\t" + str(evt.endx) + "\t" +  str(evt.ampx) + "\t" + str(evt.dur) + "\t" + str(evt.ampy) + "\t" + str(evt.midx) + "\t" + str(evt.halfdur) + "\t" +str(evt.auc) + "\t" + "\n"
        F.write(s)

def process_file(): 
    fnlist = [ARGS.filenameUF,ARGS.filenameF]
    namelist = []
    evtlist = []
    for FN in fnlist:
        # Load data
        path_filename = os.path.abspath(FN)
        filename = os.path.basename(path_filename).split('.')[0]
        namelist.append(filename)
        # Load TSV and skip header
        raw_data = np.genfromtxt(path_filename,delimiter='\t',dtype=None,encoding=None,skip_header=ARGS.sh)
        # ROI	Quadrant	Direction	Start time (s)	End time (s)	Peak time (s)	Duration (s)	Amplitude	Midpoint (s)	Half Duration(s)	AUC
        evts = []
        for row in raw_data:
            E = Evt(row)
            evts.append(E)
        evtlist.append(evts)
    return(namelist[0], namelist[1], evtlist[0],evtlist[1])

def set_check_ARGS():
    # Collect version information
    dr = os.path.dirname(os.path.abspath(__file__))
    print(dr)
    vrsn = 'Version 0.0.1'
    # Build argparser
    ap = argparse.ArgumentParser(\
        conflict_handler="resolve",
        description='To load flags from a file, type @somefile.txt. Arguments listed in order of application.',\
        epilog='For more information email rmcassidy@protonmail.com',\
        fromfile_prefix_chars='@')
    ap.add_argument("filenameUF",
                    help='input unfiltered filename (comma-separated text, include extension)')
    ap.add_argument("filenameF",
                    help='input filtered filename (comma-separated text, include extension)')
    ap.add_argument('--version','-v',
                    action='version',
                    version= vrsn)
    ap.add_argument("-o",
                    required=False,
                    metavar="filename",
                    help='output filename (no extension). Default is two file names merged together')
    ap.add_argument("--sh",
                    dest="sh",
                    metavar="lines",
                    default=2,
                    type=int,
                    help="number of lines to skip before reading as data. Default=2. Purpose is to skip non-numerical headers.")
    ARGS = ap.parse_args()
    return(ARGS)

if __name__ == "__main__":
    global ARGS
    np.set_printoptions(threshold=10)
    ARGS = set_check_ARGS()
    events = False
    
    # Process file
    uffn, ffn, UFevtsfurled, Fevtsfurled = process_file()
   
    # Unfiltered events
    UFevts_holder, Evt_seg = [],[]
    previous_roi = UFevtsfurled[0].roi
    for Evt in UFevtsfurled:
        if Evt.roi != previous_roi: UFevts_holder.append(Evt_seg); Evt_seg = []
        Evt_seg.append(Evt)
        previous_roi = Evt.roi    
        
    # Filtered events
    Fevts_holder, Evt_seg = [],[]
    previous_roi = Fevtsfurled[0].roi
    for Evt in Fevtsfurled:
        if Evt.roi != previous_roi: Fevts_holder.append(Evt_seg); Evt_seg = []
        Evt_seg.append(Evt)
        previous_roi = Evt.roi    
        
    num_segments = len(Fevts_holder)
    
    # Find the largest unfiltered amplitude (for a start and stop time in the filtered data set)
    output_evts_list = []
    selectedUFevts_counter = 0
    for x in range(0,num_segments):
        Fevts,UFevts    = Fevts_holder[x],UFevts_holder[x]
        nuf,nf          = len(UFevts),len(Fevts)
        selectedUFevts  = []
        for Fevt in Fevts:
            UFevtslice  = []
            while True: # Make UFevtslice full of all events that have their amplitude time within the Fevt time
                if len(UFevts) == 0:    break
                e = UFevts[0]
                if e.ampx < Fevt.endx:  UFevtslice.append(e); UFevts.pop(0)
                else:                   break
            if len(UFevtslice)>0:
                evti,evta = 0,0
                for i,e in enumerate(UFevtslice):
                    if abs(e.ampy) > abs(evta): evti,evta = i,e.ampy
                selectedUFevts.append(UFevtslice[evti])
        selectedUFevts_counter += len(selectedUFevts)
        output_evts_list.append(selectedUFevts)
        print("UFEvts:\t"+str(nuf)+"\tFEvts:\t"+str(nf)+"\tSelect:\t"+str(len(selectedUFevts))+"\tSegment:"+str(x))
        
    print("*\t*\t*\t*\t*\t*\t*")
    print("UFEvts:\t"+str(len(UFevtsfurled))+"\tFEvts:\t"+str(len(Fevtsfurled))+"\tSelect:\t"+str(selectedUFevts_counter)+"\t*Total*")

    F,filename = e_open(ARGS.o,uffn,ffn)
    for evt_list in output_evts_list:   
        e_out(F,evt_list, filename,uffn,ffn)
    e_close(F,filename)
    
