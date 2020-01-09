import time
import sys
import argparse
from itertools import cycle
import threading
import os
import numpy as np

from collections import deque
from bisect import insort, bisect_left
from itertools import islice

import matplotlib.pyplot as plt

class Evt(object):
    def __init__(self,id,direction,starti,endi,ampi,X,Y):
        # Indices
        self.id     = id # Number of events when initially identified
        self.dir    = direction
        self.starti = starti
        self.endi   = endi
        self.midi   = self.starti+(self.endi-self.starti)//2
        self.ampi   = ampi
        
        # X values
        self.startx = X[self.starti]
        self.endx   = X[self.endi]
        self.midx   = X[self.midi]
        self.ampx   = X[self.ampi]
        
        # Y values
        self.starty = Y[self.starti]
        self.endy   = Y[self.endi]
        self.midy   = Y[self.midi]
        self.ampy   = Y[self.ampi]
        
        # Calculated
        self.dur    = self.endx - self.startx
        self.halfdur= self.dur/2
        self.numpts = self.endi-self.starti
        
        # Added later
        self.AUC = 0
        self.prev_max_to_max_any = 0
        self.prev_max__to_max_same = 0
        self.quad = 0
        self.excluded = False

    def __str__(self):
        s="\t"
        s+= str(self.id)
        s="\t"
        s+= str(self.dir)
        s+="\t"
        s+= str(self.starti)
        s+="\t"
        s+= str(self.midi)
        s+="\t"
        s+= str(self.endi)
        s+="\t"
        s+= str(self.ampi)
        s+="\t"
        s+= str(self.numpts)
        s+="\t"
        s+= str(self.startx)
        s+="\t"
        s+= str(self.midx)
        s+="\t"
        s+= str(self.endx)
        s+="\t"
        s+= str(self.ampx)
        s+="\t"
        s+= str(self.dur)
        s+="\t"
        s+= str(self.halfdur)
        s+="\t"
        s+= str(self.starty)
        s+="\t"
        s+= str(self.midy)
        s+="\t"
        s+= str(self.endy)
        s+="\t"
        s+= str(self.ampy)
        s+="\t"
        s+= str(self.AUC)
        s+="\t"
        s+= str(self.prev_max_to_max_any)
        s+="\t"
        s+= str(self.prev_max__to_max_same)
        s+="\t"
        s+= str(self.quad)
        s+="\n"
        return(s)

class Cutoff(object):
    def __init__(self,sps,context):
        self.sps = sps
        self.x_c = 0 
        self.yc_b = 0
        self.yc_a = 0
        self.context = context
        self.evaluated = None
    def log(self,logF):
        LogF.logw('sps\tx_c\tyc_b\tyc_a\tcontext\tmethod')
        LogF.logw(self.sps,False); LogF.logw(self.x_c,False)
        LogF.logw(self.yc_b,False); LogF.logw(self.yc_a,False)
        LogF.logw(self.context,False); LogF.logw(self.evaluated)

class LogFF(object):
    def __init__(self):
        self.start_t = self.get_t()
        self.orig = sys.stdout
        self.dest = sys.stdout
    # LogF
    def logw(self,s,linebreak=True):
        sys.stdout = self.dest
        if linebreak: print(s)
        else: print(s,end=' ')
        sys.stdout = self.orig
        
    # Open/Close
    def name(self,name,terminal=False):
        self.terminal = terminal
        if not self.terminal:
            self.fn = str(name) + "_" + '.log'
            self.dest = open(self.fn,'w')
        self.logw('start time:',False)
        self.logw(self.readable_t(self.start_t))
    def close(self):
        self.end_t = self.get_t()
        self.logw('end time:',False)
        self.logw(self.readable_t(self.end_t))
        self.logw('run time (s):',False)
        self.elapse = self.end_t - self.start_t
        self.logw(self.elapse)
        if not self.terminal: self.dest.close()
        
    # Time functions
    def get_t(self):
        return(time.time())
    def readable_t(self,t):
        lt = time.localtime(t)
        s = time.strftime('date_%Y_%m_%d_time_%H_%M_%S',lt)
        return(s)
    
class PixSpin(object):
    #https://github.com/verigak/progress/blob/master/progress/__init__.py
    def __init__(self, message='Please wait...', adj_ln=True, ln = 20, ch='.', delay=0.1, suppress=False):
        self.suppress = suppress
        self.spinner = cycle(['⣾', '⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽'])
        self.delay = delay
        self.busy = False
        self.spinner_visible = False
        
        # Adjust message for standardized output size
        self.msg = message
        self.adj_ln = adj_ln # bool
        self.ln = ln # fixed length
        self.ch = ch # character to adjust by
        self.msg_len() # run check

        # Display message
        if not self.suppress: 
            sys.stdout.write(self.msg)
    
    def msg_len(self):
        if not self.suppress:
            if len(self.msg) < self.ln and self.adj_ln:
                diff = self.ln - len(self.msg)
                adj = self.ch*diff
                self.msg+=adj
            elif len(self.msg) > self.ln:
                self.msg = self.msg[:self.ln]
            
    def write_next(self):
        if not self.suppress:
            with self._screen_lock:
                if not self.spinner_visible:
                    sys.stdout.write(next(self.spinner))
                    self.spinner_visible = True
                    sys.stdout.flush()

    def remove_spinner(self, cleanup=False):
        if not self.suppress:
            with self._screen_lock:
                if self.spinner_visible:
                    sys.stdout.write('\b')
                    self.spinner_visible = False
                    if cleanup:
                        sys.stdout.write(' ')       # overwrite spinner with blank
                        sys.stdout.write('\r')      # move to next line
                    sys.stdout.flush()

    def spinner_task(self):
        if not self.suppress:
            while self.busy:
                self.write_next()
                time.sleep(self.delay)
                self.remove_spinner()

    def __enter__(self):
        if not self.suppress:
            time.sleep(0.2)
            if sys.stdout.isatty():
                self._screen_lock = threading.Lock()
                self.busy = True
                self.thread = threading.Thread(target=self.spinner_task)
                self.thread.start()

    def __exit__(self, exc_type, exc_val, exc_traceback):
        if not self.suppress:
            time.sleep(0.2)
            if sys.stdout.isatty() and not self.suppress:
                self.busy = False
                self.remove_spinner(cleanup=True)
            elif not self.suppress:
                sys.stdout.write('\r')

class Yseries(object):
    def __init__(self,Y,name,sps,quad):
        self.name = name
        self.sps = sps
        self.Y = Y
        # Defaults
        self.fitY = self.Y
        self.dfY = self.Y
        self.dff0 = self.Y
        self.CutoffList = []
        self.evts = []
        self.excluded = 0
        self.stats = []
        self.quad =quad
    def reset(self):
        self.Y = self.fitY
        self.fitY = self.Y
    def normalize(self):
        if ((self.fitY == self.Y).all()):
            self.dfY = np.array(self.Y)
            self.dff0 = np.array(self.Y)
        else:
            self.dfY = np.array(self.Y - self.fitY)
            self.dff0 = np.array(self.dfY/self.fitY) 
 
    # Calculate new self.fitY based off of self.Y
    def efa(self,alpha):
        def ewma_v_safe(data, alpha, row_size=None, dtype=None, order='C', out=None):
            #https://stackoverflow.com/questions/42869495/numpy-version-of-exponential-weighted-moving-average-equivalent-to-pandas-ewm
            """Reshapes data before calculating EWMA, then iterates once over the rows
            to calculate the offset without precision issues
            :param data: Input data, will be flattened.
            :param alpha: scalar float in range (0,1)
                The alpha parameter for the moving average.
            :param row_size: int, optional
                The row size to use in the computation. High row sizes need higher precision,
                low values will impact performance. The optimal value depends on the
                platform and the alpha being used. Higher alpha values require lower
                row size. Default depends on dtype.
            :param dtype: optional
                Data type used for calculations. Defaults to float64 unless
                data.dtype is float32, then it will use float32.
            :param order: {'C', 'F', 'A'}, optional
                Order to use when flattening the data. Defaults to 'C'.
            :param out: ndarray, or None, optional
                A location into which the result is stored. If provided, it must have
                the same shape as the desired output. If not provided or `None`,
                a freshly-allocated array is returned.
            :return: The flattened result."""
            def ewma_vectorized(data, alpha, offset=None, dtype=None, order='C', out=None):
                """Calculates the exponential moving average over a vector. Will fail for large inputs.
                :param data: Input data
                :param alpha: scalar float in range (0,1) The alpha parameter for the moving average.
                :param offset: optional The offset for the moving average, scalar. Defaults to data[0].
                :param dtype: optional  Data type used for calculations. Defaults to float64 unless data.dtype is float32, then it will use float32.
                :param order: {'C', 'F', 'A'}, optional Order to use when flattening the data. Defaults to 'C'.
                :param out: ndarray, or None, optional A location into which the result is stored. If provided, it must have the same shape as the input. If not provided or `None`, a freshly-allocated array is returned."""
                data = np.array(data, copy=False)
                if dtype is None:
                    if data.dtype == np.float32: dtype = np.float32
                    else: dtype = np.float64
                else: dtype = np.dtype(dtype)
                if data.ndim > 1: data = data.reshape(-1, order) # flatten input
                if out is None: out = np.empty_like(data, dtype=dtype)
                else:
                    assert out.shape == data.shape
                    assert out.dtype == dtype
                if data.size < 1: return out # empty input, return empty array
                if offset is None:  offset = data[0]
                alpha = np.array(alpha, copy=False).astype(dtype, copy=False)
                # scaling_factors -> 0 as len(data) gets large # this leads to divide-by-zeros below
                scaling_factors = np.power(1. - alpha, np.arange(data.shape[0] + 1, dtype=dtype), dtype=dtype)
                # create cumulative sum array
                np.multiply(data, ((alpha * scaling_factors[-2]) / scaling_factors[:-1]), dtype=dtype, out=out)
                np.cumsum(out, dtype=dtype, out=out)
                # cumsums / scaling
                out /= scaling_factors[-2::-1]
                if offset != 0:
                    offset = np.array(offset, copy=False).astype(dtype, copy=False)
                    out += offset * scaling_factors[1:]# add offsets
                return out
            def ewma_vectorized_2d(data, alpha, axis=None, offset=None, dtype=None, order='C', out=None):
                """Calculates the exponential moving average over a given axis.
                :param data: Input data, must be 1D or 2D array.
                :param alpha: scalar float in range (0,1) The alpha parameter for the moving average.
                :param axis: The axis to apply the moving average on. If axis==None, the data is flattened.
                :param offset: optional The offset for the moving average. Must be scalar or a vector with one element for each row of data. If set to None, defaults to the first value of each row.
                :param dtype: optional Data type used for calculations. Defaults to float64 unless data.dtype is float32, then it will use float32.
                :param order: {'C', 'F', 'A'}, optional Order to use when flattening the data. Ignored if axis is not None.
                :param out: ndarray, or None, optional A location into which the result is stored. If provided, it must have the same shape as the desired output. If not provided or `None`,a freshly-allocated array is returned."""
                data = np.array(data, copy=False)
                assert data.ndim <= 2
                if dtype is None:
                    if data.dtype == np.float32: dtype = np.float32
                    else: dtype = np.float64
                else: dtype = np.dtype(dtype)
                if out is None: out = np.empty_like(data, dtype=dtype)
                else:
                    assert out.shape == data.shape
                    assert out.dtype == dtype
                if data.size < 1: return out # empty input, return empty array
                if axis is None or data.ndim < 2: # use 1D version
                    if isinstance(offset, np.ndarray): offset = offset[0]
                    return ewma_vectorized(data, alpha, offset, dtype=dtype, order=order, out=out)
                assert -data.ndim <= axis < data.ndim
                # create reshaped data views
                out_view = out
                if axis < 0: axis = data.ndim - int(axis)
                if axis == 0: data,out_view = data.T,out_view.T # transpose data views so columns are treated as rows
                if offset is None: offset = np.copy(data[:, 0])# use the first element of each row as the offset
                elif np.size(offset) == 1: offset = np.reshape(offset, (1,))
                alpha = np.array(alpha, copy=False).astype(dtype, copy=False)
                # calculate the moving average
                row_size,row_n = data.shape[1],data.shape[0]
                scaling_factors = np.power(1. - alpha, np.arange(row_size + 1, dtype=dtype),dtype=dtype)
                # create a scaled cumulative sum array
                np.multiply(data, np.multiply(alpha * scaling_factors[-2], np.ones((row_n, 1), dtype=dtype), dtype=dtype)/scaling_factors[np.newaxis, :-1], dtype=dtype, out=out_view)
                np.cumsum(out_view, axis=1, dtype=dtype, out=out_view)
                out_view /= scaling_factors[np.newaxis, -2::-1]
                if not (np.size(offset) == 1 and offset == 0):
                    offset = offset.astype(dtype, copy=False) # add the offsets to the scaled cumulative sums
                    out_view += offset[:, np.newaxis] * scaling_factors[np.newaxis, 1:]
                return out
            def get_max_row_size(alpha, dtype=float):
                assert 0. <= alpha < 1.
                # This will return the maximum row size possible on your platform for the given dtype. I can find no impact on accuracy at this value on my machine.
                epsilon = np.finfo(dtype).tiny # If this produces an OverflowError, make epsilon larger
                return int(np.log(epsilon)/np.log(1-alpha)) + 1
            
            data = np.array(data, copy=False)
            if dtype is None:
                if data.dtype == np.float32: dtype = np.float32
                else: dtype = np.float
            else: dtype = np.dtype(dtype)
            if row_size is not None:row_size = int(row_size)
            else: row_size = int(get_max_row_size(alpha, dtype))
            if data.size <= row_size: return ewma_vectorized(data, alpha, dtype=dtype, order=order, out=out) # The normal function can handle this input, use that
            if data.ndim > 1: data = np.reshape(data, -1, order=order) # flatten input
            if out is None: out = np.empty_like(data, dtype=dtype)
            else:
                assert out.shape == data.shape
                assert out.dtype == dtype
            row_n = int(data.size // row_size)  # the number of rows to use
            trailing_n = int(data.size % row_size)  # the amount of data leftover
            first_offset = data[0]
            if trailing_n > 0: out_main_view,data_main_view= np.reshape(out[:-trailing_n], (row_n, row_size)),np.reshape(data[:-trailing_n], (row_n, row_size)) # set temporary results to slice view of out parameter
            else: out_main_view,data_main_view = out,data
            # get all the scaled cumulative sums with 0 offset
            ewma_vectorized_2d(data_main_view, alpha, axis=1, offset=0, dtype=dtype, order='C', out=out_main_view)
            scaling_factors = (1 - alpha) ** np.arange(1, row_size + 1)
            last_scaling_factor = scaling_factors[-1]
            # create offset array
            offsets = np.empty(out_main_view.shape[0], dtype=dtype)
            offsets[0] = first_offset
            # iteratively calculate offset for each row
            for i in range(1, out_main_view.shape[0]): offsets[i] = offsets[i - 1] * last_scaling_factor + out_main_view[i - 1, -1]
            # add the offsets to the result
            out_main_view += offsets[:, np.newaxis] * scaling_factors[np.newaxis, :]
            if trailing_n > 0: ewma_vectorized(data[-trailing_n:], alpha, offset=out_main_view[-1, -1], dtype=dtype, order='C', out=out[-trailing_n:])# process trailing data in the 2nd slice of the out parameter
            return out
        
        Y = self.Y
        fY = ewma_v_safe(Y,float(alpha))
        bY = np.flip(ewma_v_safe(np.flip(Y),float(alpha)))
        aY = (fY - bY)/2; Y = Y - aY
        chk = [x for x in ARGS.filt if 'efs' in x]
        if len(chk)>0: Y+=float(chk[0][1])
        self.fitY= np.array(Y)        
    def pass_filter(self,fc_list,method):
        Y = self.Y
        # Determine combination of methods
        if method == 'lpf':
            u_lpf,u_hpf,u_bpf,u_brf = True,False,False,False
            fc_lowpass,fc_highpass,b =  fc_list[0], None,       fc_list[1]
        if method == 'hpf':
            u_lpf,u_hpf,u_bpf,u_brf = False,True,False,False
            fc_lowpass,fc_highpass,b =  None,       fc_list[0], fc_list[1]
        if method == 'bpf':
            u_lpf,u_hpf,u_bpf,u_brf = True,True,True,False
            fc_lowpass,fc_highpass,b =  fc_list[0], fc_list[1], fc_list[2]
        if method == 'brf':
            u_lpf,u_hpf,u_bpf,u_brf = True,True,False,True
            fc_lowpass,fc_highpass,b =  fc_list[0], fc_list[1], fc_list[2]
        
        # Calculate transition frequency
        if b is None:
            if fc_lowpass is not None: 
                b = 0.95*float(fc_lowpass)
            else: 
                b = 0.95*float(fc)
        
        # Prepare template
        N = int(np.ceil(4/b))
        if N%2 != 0: N+=1 # make odd
        n = np.arange(N)
        
        if u_lpf: # Compute a low-pass filter.
            hlpf = np.sinc(2*float(fc_lowpass)*(n-(N-1)/2))
            hlpf = hlpf*np.blackman(N)
            hlpf = hlpf/np.sum(hlpf) 
        if u_hpf: # Invert for high pass filter
            h1 = np.sinc(2*float(fc_highpass)*(n-(N-1)/2))
            h1 = h1*np.blackman(N)
            h1 = h1/np.sum(h1) 
            hhpf = h1*-1
            hhpf[(N-1)//2]+=1
        # Select h filters    
        if u_bpf:   h = np.convolve(hlpf,hhpf) # Convolve filters
        elif u_brf: h = hlpf + hhpf   # Add filters         
        elif u_hpf: h = hhpf
        else:       h = hlpf 

        Yf = np.array(np.convolve(Y,h,'valid'))
            
        # Fix ends
        N = Y.shape[0] - Yf.shape[0]
        if N%2 != 0: N+=1 # make odd
        si = int(np.ceil(N/2))-1
        ss = int(-1*np.floor(N/2))
        
        # Return
        nY = np.array(np.concatenate((Yf[:si],Yf,Yf[ss:])))
        if len(nY) != len(Y):
            diff = len(nY) - len(Y)
            while diff != 0:
                if diff < 0: nY = np.array(np.concatenate(([nY[0]],nY)))
                if diff > 0: nY = np.array(np.concatenate((nY,[nY[-1]])))
                diff = len(nY) - len(Y)
                print(diff,[nY[0]],[nY[-1]])
                
        self.fitY = nY        
    def run_mean(self,window_size):
        #https://stackoverflow.com/questions/37671432/how-to-calculate-running-median-efficiently
        seq = self.Y
        seq = iter(seq); d = deque()
        s = []; result = []
        for item in islice(seq, window_size):
            d.append(item); insort(s, item)
            result.append(np.mean(s))
        m = window_size // 2
        for item in seq:
            old = d.popleft(); d.append(item)
            del s[bisect_left(s, old)]; insort(s, item)
            result.append(np.mean(s))
        self.fitY = np.array(result)
    def run_median(self,window_size):
        #https://stackoverflow.com/questions/37671432/how-to-calculate-running-median-efficiently
        seq = self.Y
        seq = iter(seq); d = deque()
        s = []; result = []
        for item in islice(seq, window_size):
            d.append(item); insort(s, item)
            result.append(s[len(d)//2])
        m = window_size // 2
        for item in seq:
            old = d.popleft(); d.append(item)
            del s[bisect_left(s, old)]
            insort(s, item)
            result.append(s[m])
        self.fitY = np.array(result)    
    def lsq_linear(self,X):
        A = np.array([X,np.ones(len(X))])
        m,c = np.linalg.lstsq(A.T,self.Y,rcond=None)[0]
        fit_Y = []
        for n in X: fit_Y.append(((m*n)+c))
        self.fitY = np.array(fit_Y)
    def mean(self):
        self.fitY = np.repeat(np.mean(self.Y),len(self.Y))
    def median(self):
        self.fitY = np.repeat(np.median(self.Y),len(self.Y))
    def peakfit(self,dir):
        Y = self.Y
        E = self.evts
        if dir =='a':
            pidx = [evt.ampi for evt in E if evt.dir =='a']
        elif dir =='b':
            pidx = [evt.ampi for evt in E if evt.dir =='b']
        else:
            return(Y)
        
        # No events
        if len(pidx)==0: 
            Ym = np.median(Y)
            return(Y)
        # Generate lines connecting peaks
        fit = []
        if len(pidx)>1:
            for i in range(1,len(pidx)):
                dist = pidx[i] - pidx[i-1]
                Yn = np.linspace(Y[pidx[i-1]],Y[pidx[i]],dist)
                fit.extend(Yn)
        else: # Just one event
            pidx.insert(0,0)
            pidx.append(len(Y)-1)
        
        # Last event to end
        points = [(pidx[-2],Y[pidx[-2]]),(pidx[-1],Y[pidx[-1]])]
        x_coords, y_coords = zip(*points)
        A = np.vstack([x_coords,np.ones(len(x_coords))]).T
        m, c = np.linalg.lstsq(A, y_coords,rcond=None)[0]
        fit.extend([m*n+c for n in range(pidx[-1],len(Y))])
        
        # Start to first event
        points = [(pidx[0],Y[pidx[0]]),(pidx[1],Y[pidx[1]])]
        x_coords, y_coords = zip(*points)
        A = np.vstack([x_coords,np.ones(len(x_coords))]).T
        m, c = np.linalg.lstsq(A, y_coords,rcond=None)[0]
        fit_y = [m*n+c for n in range(0,pidx[0])]
        fit_y.extend(fit)
        fit_y = np.array(fit_y)
        self.fit_y = fit_y
    
    # Event functions
    def evt_Y(self,evaluated):
        if evaluated == 'raw':
            return(self.Y)
        elif evaluated == 'fity':
            return(self.fitY)
        elif evaluated == 'dfy':
            return(self.dfY)
        elif evaluated == 'dff0':
            return(self.dff0)
        else:
            return(self.Y)
    def identify_events(self,X,context):    
        Cut = [x for x in self.CutoffList if x.context==context][0]
        Y = self.evt_Y(Cut.evaluated)
        above, below = False, False
        pt_ctr = 0
        evt_l = []
        for i in range(0,len(Y)):
            n = round(Y[i],20)
            if n>=0:
                if not above: # Start new above event or complete old below event
                    if not below: # Start new event
                        starti=i; ampi=i; above=True;below=False; pt_ctr+=1
                    else: # Complete below event
                        if abs(Y[ampi])>=abs(Cut.yc_b) and pt_ctr>=Cut.x_c: # Save if meets cutoff
                            evt_l.append(Evt(len(evt_l),'b',   starti,    i,  ampi,   X,  Y))
                        below = False; pt_ctr = 0
                else: # Update above event
                    if abs(n)>abs(Y[ampi]): ampi=i
                    pt_ctr+=1                    
            else:
                if not below:
                    if not above:
                        starti=i; ampi=i; below=True; above=False; pt_ctr+=1
                    else:
                        if abs(Y[ampi])>=abs(Cut.yc_a) and pt_ctr>=Cut.x_c: 
                            evt_l.append(Evt(len(evt_l),'a',   starti,    i,  ampi,   X,  Y))
                        above = False; pt_ctr = 0
                else:
                    if abs(n)>abs(Y[ampi]): ampi=i
                    pt_ctr+=1
        # Handle end case
        if above:
            if abs(Y[ampi])>=abs(Cut.yc_a) and pt_ctr>=Cut.x_c:  
                            evt_l.append(Evt(len(evt_l),'a',   starti,    i,  ampi,   X,  Y))
        if below:
            if abs(Y[ampi])>=abs(Cut.yc_b) and pt_ctr>=Cut.x_c: 
                            evt_l.append(Evt(len(evt_l),'b',   starti,    i,  ampi,   X,  Y))
        self.evts = evt_l
    def exclude_replace_events(self,X,Cut):
        Y = self.evt_Y(Cut.evaluated)
        indices = range(0,len(Y))
        exclude = []
        self.excluded = 0
        for e in self.evts:
            add = False
            if Cut.x_c is not None and e.numpts>=Cut.x_c: add = True; self.excluded+=1
            elif Cut.yc_b is not None and e.dir == 'b' and abs(Y[e.ampi])>=abs(Cut.yc_b): add = True; self.excluded+=1
            elif Cut.yc_a is not None and e.dir == 'a' and abs(Y[e.ampi])>=abs(Cut.yc_a): add = True; self.excluded+=1
            if add:
                e.excluded=True
                exclude.extend(range(e.starti,e.endi))
        
        retain = set(indices) - set(exclude)
        retain = list(retain)
        retain.sort()
        
        # Confirm start/end indices are included if the events do not totally cross the space
        if retain[0] != indices[0]:   retain.insert(0,indices[0])
        if retain[-1] != indices[-1]: retain.append(indices[-1])
        
        # Recreate data lines
        nY = [self.Y[retain[0]]]
        nfitY = [self.fitY[retain[0]]]
        for i in range(1,len(retain)):
            dist = retain[i] - retain[i-1]
            if dist > 1: #indicates a skipped section
                t1 = np.linspace(self.Y[retain[i-1]],self.Y[retain[i]],dist)
                t2 = np.linspace(self.fitY[retain[i-1]],self.fitY[retain[i]],dist)
                nY.extend(t1)
                nfitY.extend(t2)
            else:
                nY.append(self.Y[retain[i]])
                nfitY.append(self.fitY[retain[i]])
                
        self.Y = np.array(nY)
        self.fitY = np.array(nfitY)
        self.normalize()
    def characterize_events(self):
        Cut = self.CutoffList[-1]
        Y = self.evt_Y(Cut.evaluated)
        # AUC
        for E in self.evts:
            E.AUC = np.trapz(Y[E.starti:E.endi])
        
        #Previous max amp to current max amp
        for i, E in enumerate(self.evts):
            if i==0: E.prev_max_to_max_any=0
            else: E.prev_max_to_max_any= self.evts[i].ampx - self.evts[i-1].ampx

        #Previous max amp to current max amp same type
        ai,bi = 0,0
        ac,bc = 0,0
        sumauca,sumaucb = 0,0
        for i, E in enumerate(self.evts):
            if E.dir == 'a':
                ac+=1
                sumauca+=self.evts[i].AUC
                if ac <= 1: E.prev_max__to_max_same = 0
                else: E.prev_max__to_max_same = self.evts[i].ampx - self.evts[ai].ampx
                ai = i
            else:
                bc+=1
                sumaucb+=self.evts[i].AUC
                if bc <= 1: E.prev_max__to_max_same = 0
                else: E.prev_max__to_max_same = self.evts[i].ampx - self.evts[bi].ampx
                bi = i
                
        #Determine quadrant and apply name
        xcutoff=self.quad[0]
        ycutoff=self.quad[1]
        for i, E in enumerate(self.evts):
            amp = E.ampy
            dur = E.dur
            #quad 1
            if dur < xcutoff and amp < ycutoff:
                E.quad=1
            #quad 2
            elif dur > xcutoff and amp < ycutoff:
                E.quad=2
            #quad 3
            elif dur < xcutoff and amp > ycutoff:
                E.quad=3   
            #quad 4
            elif dur > xcutoff and amp > ycutoff:
                E.quad=4
            else:
                E.quad=0
        
        self.stats = [sumaucb,sumauca,bc,ac]

    # Other
    def log(self,LogF):
        LogF.logw("Name:",False);       LogF.logw(self.name)
        LogF.logw("Y:",False);          LogF.logw(self.Y,False)
        LogF.logw("\tLength:",False);   LogF.logw(len(self.Y))
        LogF.logw("fitY:",False);       LogF.logw(self.fitY,False)
        LogF.logw("\tLength:",False);   LogF.logw(len(self.fitY))        
        LogF.logw("dfY:",False);        LogF.logw(self.dfY,False)
        LogF.logw("\tLength:",False);   LogF.logw(len(self.dfY))
        LogF.logw("dff0:",False);       LogF.logw(self.dff0,False)
        LogF.logw("\tLength:",False);   LogF.logw(len(self.dff0))    
    def elog(self,LogF):
        LogF.logw("Name:",False);       LogF.logw(self.name)
        LogF.logw("Num evts:",False);   LogF.logw(len(self.evts))

    def re(self):
        return

def make_plot(X, Y_M, filename,names,S):
    # Name file
    filename +="_plot_"

    # Plot loop (Y_M dependent)
    for i in range(0,len(Y_M)):
        subplotname = filename+str(names[i])
        # Open plot objects
        plt.figure()
        ax = plt.subplot(111); ax.set_title(subplotname)
        
        # Output file data matrix
        out = [X]
    
        # Plot desired subsets of data     
        if 'raw' in S:
            ax.plot(        X,  Y_M[i].Y,     linewidth=2,    alpha=0.7,  label='raw')
            out.append(     Y_M[i].Y)
        if 'fity' in S:
            ax.plot(        X,  Y_M[i].fitY,  linewidth=2,    alpha=0.7,  label='fity')
            out.append(     Y_M[i].fitY)        
        if 'dfy' in S:
            ax.plot(        X,  Y_M[i].dfY,   linewidth=2,    alpha=0.7,  label='dfy')
            out.append(     Y_M[i].dfY)        
        if 'dff0' in S:
            ax.plot(        X,  Y_M[i].dff0,  linewidth=2,    alpha=0.7,  label='dff0')
            out.append(     Y_M[i].dff0)    

        out = np.array(out)
        
        # Add additional graph elements
        if np.min(out)<0 and np.max(out)>0: ax.axhline(y=0,color='black') # add zero line if plotted data set crosses zero 
        if 'evts' in S:
            aE = [E for E in Y_M[i].evts if E.dir=='a' and not E.excluded]
            bE = [E for E in Y_M[i].evts if E.dir=='b' and not E.excluded]
            astartx= [E.startx  for E in aE]; astarty= [E.starty  for E in aE]
            aampx  = [E.ampx    for E in aE]; aampy  = [E.ampy    for E in aE]
            aendx  = [E.endx    for E in aE]; aendy  = [E.endy    for E in aE]
            bstartx= [E.startx  for E in bE]; bstarty= [E.starty  for E in bE]
            bampx  = [E.ampx    for E in bE]; bampy  = [E.ampy    for E in bE]
            bendx  = [E.endx    for E in bE]; bendy  = [E.endy    for E in bE]
            ax.scatter(astartx,    astarty,    marker='>', color='black',  s=20)
            ax.scatter(aampx,      aampy,      marker='^', color='black',  s=75)
            ax.scatter(aendx,      aendy,      marker='<', color='black',  s=20)
            ax.scatter(bstartx,    bstarty,    marker='>', color='black',  s=20)
            ax.scatter(bampx,      bampy,      marker='^', color='black',  s=75)
            ax.scatter(bendx,      bendy,      marker='<', color='black',  s=20)
        if 'excl_evts' in S: # Plots excluded events
            aE = [E for E in Y_M[i].evts if E.dir=='a' and E.excluded]
            bE = [E for E in Y_M[i].evts if E.dir=='b' and E.excluded]
            astartx= [E.startx  for E in aE]; astarty= [E.starty  for E in aE]
            aampx  = [E.ampx    for E in aE]; aampy  = [E.ampy    for E in aE]
            aendx  = [E.endx    for E in aE]; aendy  = [E.endy    for E in aE]
            bstartx= [E.startx  for E in bE]; bstarty= [E.starty  for E in bE]
            bampx  = [E.ampx    for E in bE]; bampy  = [E.ampy    for E in bE]
            bendx  = [E.endx    for E in bE]; bendy  = [E.endy    for E in bE]
            ax.scatter(astartx,    astarty,    marker='>', color='red',  s=20)
            ax.scatter(aampx,      aampy,      marker='^', color='red',  s=75)
            ax.scatter(aendx,      aendy,      marker='<', color='red',  s=20)
            ax.scatter(bstartx,    bstarty,    marker='>', color='red',  s=20)
            ax.scatter(bampx,      bampy,      marker='^', color='red',  s=75)
            ax.scatter(bendx,      bendy,      marker='<', color='red',  s=20)  
            
        # Set legend
        ax.legend(loc='upper right')
        
        # Set ticks
        arg_list = [i for i in S]
        while len(arg_list)>0:
            method,mod,arg_list = return_method(arg_list)
            if method =='xtick'     : ax.xticks(np.arange(0,max(X),mod))
            if method =='ytick'     : ax.yticks(np.arange(np.min(Y_M[i]),np.max(Y_M[i]),mod))
            if method =='ylim'      : ax.ylim(mod[0],mod[1])                               
            if method =='xlim'      : ax.xlim(mod[0],mod[1])                               
            if method =='save_csv'  : 
                print('save_csv')
                np.savetxt(subplotname+".csv",np.array(out).T,delimiter=',',fmt="%s")                               
            if method =='save_png'  : plt.savefig(subplotname,dpi=mod)                               
        
def e_formatted_out(X, Y_M, filename,names):
    # Name file
    filename+="_evts_formatted.txt"
    F = open(filename,"w")
    
    # Write out headers
    F.write("\t\t\t\t\t\t\t\t\t\t"+filename+"\n")
    F.write("ROI\tQuadrant\tDirection\tStart time (s)\tEnd time (s)\tPeak time (s)\tDuration (s)\tAmplitude\tMidpoint (s)\tHalf Duration(s)\tAUC\n")

    for i,Y in enumerate(Y_M):
        for evt in Y.evts:
            s = names[i] + "\t" + str(evt.quad)+ "\t" + str(evt.dir) + "\t" + str(evt.startx) + "\t" + str(evt.endx) + "\t" +  str(evt.ampx) + "\t" + str(evt.dur) + "\t" + str(evt.ampy) + "\t" + str(evt.midx) + "\t" + str(evt.halfdur) + "\t" +str(evt.AUC) + "\t" + "\n"
            F.write(s)

def e_out(X, Y_M, filename,names):
    # Generate files
    tl = [str(str(filename)+"_data_"+str(name)+"_evts.txt") for name in names]
    filenames = [open(t,"w") for t in tl]

    # Write out headers    
    for of in filenames: 
        of.write("methods applied:"+str(vars(ARGS))+"\n")
    for of in filenames: 
        of.write("summary statistics key:\t"+\
            "y mean\t"+\
            "y sd\t"+\
            "dfy mean\t"+\
            "dfy sd\t"+\
            "dff0 mean\t"+\
            "dff0 sd\t"+\
            "num below\t"+\
            "num above\t"+\
            "sum below AUC\t"+\
            "sum above AUC\t"+\
            "xc\t"+\
            "yc_b\t"+\
            "yc_a\t"+\
            "xvals-per-sample\n")
        
    # Write out summary statistics
    for c,of in enumerate(filenames):
        of.write(Y_M[c].__str__())
        
    #Write out event data
    for c,of in enumerate(filenames):
        of.write("event info key:\t"+\
            "direction (above/below reference line aka type)\t"+\
            "start idx\t"+\
            "mid idx\t"+\
            "end idx\t"+\
            "max amp idx\t"+\
            "num samples\t"+\
                
            "start x\t"+\
            "mid x\t"+\
            "end x\t"+\
            "max amp x\t"+\
            "duration x\t"+\
            "half-duration x\t"+\
                
            "start y\t"+\
            "mid y\t"+\
            "end y\t"+\
            "max amp y\t"+\

            "AUC\t"+\
            "previous max amp (any type) to this max amp x\t"+\
            "previous max amp (same type) to this max amp x\t"+\
            "quadrant\n")
        for E in Y_M[c].evts:
            of.write(E.__str__())
        of.close()

def return_evaluated(arg_list):
    for entry in arg_list:
        if 'fity' in entry: return('fity')
        if 'dfy' in entry:  return('dfy')
        if 'dff0' in entry: return('dff0')
        if 'raw' in entry:  return('raw')
    return(None)
    
def return_cutoffs(sps,Y,arg_list,context):
    Coff = Cutoff(sps,context)
    # Resolve x cutoff
    for entry in arg_list:
        if 'xcs' in entry:
            xcs=float(entry[1])   
            Coff.x_c = xcs*sps
        if 'xc' in entry:
            xc=float(entry[1])
            Coff.x_c = xc
    
    # Resolve y cutoff
    for entry in arg_list:   
        if 'yc' in entry:
            ycb=entry[1]
            yca=entry[2]
            if ycb != '': Coff.yc_b = float(ycb)
            if yca != '': Coff.yc_a = float(yca)
        if 'yp' in entry:
            ypb=entry[1]
            ypa=entry[2]  
            if ypb != '': Coff.yc_b = np.quantile(Y,float(ypb))
            if ypa != '': Coff.yc_a = np.quantile(Y,float(ypa))
        if 'ystd' in entry:
            ystdb=entry[1]
            ystda=entry[2] 
            if ystdb != '': Coff.yc_b = np.mean(Y)-np.std(Y)*float(ystdb)
            if ystda != '': Coff.yc_a = np.mean(Y)+np.std(Y)*float(ystda)
    
    return(Coff)

def return_method(arg_list):
    LogF.logw('return_method()')
    method = None
    extra = None
    a = arg_list.pop(0)
    if 'efa' in a: 
        method = 'efa'
        extra = float(a[1])
    elif 'lpf' in a: 
        method = 'lpf'
        if len(a)==3: extra = [float(a[1]),float(a[2])]
        else: extra = [float(a[1]),None]
    elif 'hpf' in a: 
        method = 'hpf'
        if len(a)==3: extra = [float(a[1]),float(a[2])]
        else: extra = [float(a[1]),None]
    elif 'bpf' in a: 
        method = 'bpf'
        if len(a)==4: extra = [float(a[1]),float(a[2]),float(a[3])]
        else: extra = [float(a[1]),float(a[2]),None]
    elif 'brf' in a: 
        method = 'brf'
        if len(a)==4: extra = [float(a[1]),float(a[2]),float(a[3])]
        else: extra = [float(a[1]),float(a[2]),None]
    elif 'rmn' in a: 
        method = 'rmn'
        extra = int(a[1])
    elif 'rmd' in a: 
        method = 'rmd'
        extra = int(a[1])
    elif 'mean' in a: 
        method = 'mean'
        extra = None
    elif 'med' in a: 
        method = 'median'
        extra = None
    elif 'lsq' in a: 
        method = 'lsq'
        extra = None
    elif 'xtick' in a: 
        method = 'xtick'
        extra = float(a[1])    
    elif 'ytick' in a: 
        method = 'ytick'
        extra = float(a[1])    
    elif 'xlim' in a: 
        method = 'xlim'
        extra = [float(a[1]),float(a[2])]    
    elif 'ylim' in a: 
        method = 'ylim'
        extra = [float(a[1]),float(a[2])]    
    elif 'save_csv' in a:
        method = 'save_csv'
        extra = None   
    elif 'save_png' in a:
        method = 'save_png'
        extra = None  
    elif 'a' in a or 'above' in a: 
        method = 'a'
        extra = None
    elif 'b' in a or 'below' in a: 
        method = 'b'
        extra = None
    return(method,extra,arg_list)

def process_file(): 
    LogF.logw('process_file()')

    # Load data
    path_filename = os.path.abspath(ARGS.filename)
    filename = path_filename.split(".")[0]

    # Load CSV and skip header
    raw_data = np.genfromtxt(path_filename,delimiter=',',dtype=None,encoding=None,skip_header=ARGS.sh)

    # Input matrix is variable, cannot be transposed - isolate out columns into rows 
    x_y_raw = [[row[c] for row in raw_data] for c in ARGS.c] 

    if ARGS.r is not None: 
        #Get unique names in order
        name_raw = [row[int(ARGS.r[0])] for row in raw_data]
        all_names = []
        for nm in name_raw:
            if nm not in all_names: all_names.append(nm)
            
        #Create index coordinate matrix of values per name
        coordinate_matrix = []
        for nm in all_names:
            nm_idx = []
            for i,nm_raw in enumerate(name_raw):
                if nm_raw == nm: nm_idx.append(i)
            coordinate_matrix.append(nm_idx)
            
        #Rearrange data
        yselect = []
        xselect = np.array([x_y_raw[0][i] for i in coordinate_matrix[0]],dtype=float) #append time
        for row in coordinate_matrix: yselect.append(np.array([x_y_raw[1][i] for i in row],dtype=float))
        yselect = np.array(yselect,dtype=float)

    else:
        xselect = np.array(x_y_raw[0],dtype=float)
        yselect = np.array(x_y_raw[1:],dtype=float)
        all_names = ['col_'+str(i) for i in ARGS.c[1:]]

    LogF.logw('filename:',False); LogF.logw(filename)
    LogF.logw('X:',False);        LogF.logw(xselect) 
    LogF.logw('Ydata:',False);    LogF.logw(yselect) 
    LogF.logw('names:',False);    LogF.logw(all_names)

    return(filename, xselect, yselect, all_names)

def readme():
    s="""\
Expansion of things seen in help message (NOTE - REFER TO IN PROGRAM HELP MESSAGE 
FOR MOST UP TO DATE INFORMATION)
-i      Input file name. Include extension, must be csv format
-o      Output file name. No extension necessary
-c      If using -r: first column entry is x, second is loc of Y value. Default is 0 1. 
        If first column entry is x. second is signal 1, third is signal
        2, etc. Default is 0 1
-r      Enter in row names to separate into data columns. First entry is column with 
        row names, 
        -r 0 ID1 ID2 ID5
        To use all uniquely named rows 
        -r 3 useall 
        If no row names are given, all rows are used and data columns are named 
        by the reference 
--sh    skip headers: number of rows to skip from top of .csv. Default is 1.
-------------------------------------------------------------------------------
--ds    Factor by which to downsample input data file. Larger factors > fewer
        points remain. Default if invoked is 2,skipping every other item.
                rawdat= [[t0 t1  t2  t3  t4  t5  t6  t7  t8  t9 t10 t11]
                        [A0 A1  A2  A3  A4  A5  A6  A7  A8  A9 A10 A11]
                        [C0 C1  C2  C3  C4  C5  C6  C7  C8  C9 C10 C11]]
        --ds 2 #keeps every 2nd element                         
                dsdat = [[t0     t2      t4      t6      t8     t10    ]
                        [A0     A2      A4      A6      A8     A10    ]
                        [C0     C2      C4      C6      C8     C10    ]] 
        --ds 10 #keeps every 10th element                       
                dsdat = [[t0                                    t10    ]
                        [A0                                    A10    ]
                        [C0                                    C10    ]]
        --ds 0.3 #keeps every 0.3 element (i.e. remove every 3rd element)
                dsdat = [[   t1  t2      t4  t5      t7  t8     t10    ]
                        [   A1  A2      A4  A5      A7  A8     A10    ]
                        [   C1  C2      C4  C5      C7  C8     C10    ]] 
--fdiv  Enter in a factor by which to divide each column of data. Same ordering
        principle as rdiv. e.g. -r 0 4A 5A 2A --fdiv 3000.1 4000 5000. divides
        4A by 3000.1, 5A by 4000, and 2A by 5000
--rdiv  Type the row name exactly as it appears in -r by which to divide other
        rows. For example, when writing -c 13 1 -r 0 1A 5A 2A --rdiv 2A, this
        means that the time values are in column 13 of the  original data, the 
        y values are in column 1 of the orig data, the row names are in column
        0 of the orig data, and rownames 1A, 5A, and 2A will be loaded for 
        more analysis. E.g.                                
        data =  [[1A0            1A1             1An]            
                [5A0            5A1             5An]]           
        rdata = [[1A0/2A0        1A1/2A1         1An/2An]        
                [5A0/2A0        5A1/2A1         5An/2An]]       
                The 2A row will be excluded
        (note this must be carefully evaluated - please look at verbose output
        to confirm what has been done to data.)
--trim  Removes n x values from start and the end of each seg 
        --trim 0 10 removes 0 x values form beginning, 10 xvals from the end.
--filt  Apply filters to data prior to normalization.           
        --filt rmn,101      Uses a running mean of set window size to smooth 
                            raw data prior to analysis
        --filt rmd,51       Uses a running median of set window size to smooth
                            raw data prior to analysis
        --filt efa,0.00003  Use exponential filter, which functions similar to
                            a running mean/median. Range 0<alpha<1, proportion
                            influence value N has on exp filt v,val Nl N-1, 
                            Default alpha is 0.00003
        --filt efa,0.00003  Add a shift from 0 on y-axis after exp. filt is
                            applied. Default is 1                             
        --filt lpf,0.005    Use low-pass filter to eliminate high freq noise
                            using sinc function and blackman window. Fc is 
                            cutoff frequency for low pass filter; cycles/sec 
                            proportional to sampling rate; def is 0.005 
                            (5hz with 1ksps). b (transition frequency transFc)
                            is automatically calculated as 0.95 of fc; 
-------------------------------------------------------------------------------        
--norm calculates a fity, dfy, and dff0 using one of 5 methods. 
    mean Normalize by mean of the input Y
    med  Normalize by median of the input Y"
    rmn,N   Use a running mean of set window size ( in sample #) to generate 
            ref line. Recommend window size 10x larger than expected event size. 
            Default is 1000 
    rmd,N   Use a running median of set window size (sample #) generate ref line
            Recommend window size 10x larger than expected event size. 
            Default is 1000
    lsq   Use linear least-squares regress, fit primary signal to itself
    EXAMPLES:
        --norm mean
        --norm nmn,50
--evts  Identify events using the given parameters and given 'raw' line.  
        UNITS ARE DIRECTIONAL - INCLUDE SIGNS
    --evts  dfy xc,1 yc,0,0     <--- DEFAULT  
    --evts  dff0    --evts dfy  --evts fity                              
    --evts  dfy xc,2 uses an x cutoff of 2 x values(usually seconds) to include              
    --evts  dfy xcs,1000 uses a sample# cutoff.              
    --evts  dfy yc,-1,1 uses y value cutoffs of -1,1 for amplitude of a/b waves               
    --evts  dfy yp,1,99 uses y percentace cutoffs            
    --evts  dfy ys,1 uses +- standard dev    [np median+-(Factor)*standard-dev]           
    --evts  dfy yn means no events are found
--excl if invoked, can exclude waves above a threshold (e.g. action 
        potentials) with peak amplitude bigger than yc. yc method options 
        are the same as in --evts, except this will only cut off of values 
        greater in magnitude than the given yc.
        After exclusion, the program uses linear regression to fill in missing 
        Y values. fity is recalcd using the edited Y dataset. 
        
        Both above and below waves can be excluded. Formatting is the same as
        in --evts; if you only want to exclude one type of waves, leave an 
        empty comma for the others.
        
        UNITS ARE IN MAGNITUDE, NOT DIRECTIONAL.
    EXAMPLES:
    --excl yp,,80 removes all above waves with amplitudes in the top 20%
        and fills in missing Y values using lsq. It does nothing to the below
    --excl yc,1, removes all below waves with amplitudes less than 1 y value
        and fills in missing Y values using lsq. It does nothing to the above.
    --excl yc,,0.05 removes all waves with amplitudes above the Y value of
        0.05. Please note the units are relative to what reference line was
        selected for --evts. E.g. dff0 is in percentile, whereas dfy is in
        units Y above 0.
--renorm  The method of norming to use again takes the same inputs as --norm, 
        with the addition of aligning to peaks of events calculated from
        above or below using ---renorm a or --renorm b. This uses the same
        data line as was used for --evts. Generally only used if --excl is
        used or if desiring to re-calibrate to just above or below waves.
    EXAMPLES:    
    --renorm above (normalizes to peaks (a))  
    --renorm below (troughs(b=below))               
    --excl yp,,80 --renorm rmn,50 
        removes all waves with amplitudes in the top 20% and calculates new 
        fity, dfy, dff0 using a running mean of 50 samples.
    --renorm lsq
--reevts used after renormalizaztion, same as --evts
--quad  Enter in raw x and y values used to divide into quadrants. e.g.
    --quad 1,0.5
        X-cutoff(1) Y-cutoff(0.5)   Quadrant
        below       below           1
        above       below           2
        below       above           3
        above       above           4
        n.b. processed as absolute units    
-------------------------------------------------------------------------------
-p      Display plots with interactive viewer
--plot  inclusive options: [a raw fity dfy dff0 evts excl_evts xlim,<min>,<max> 
        ylim,<min>,<max> xtick,<interval> ytick,<interval> save_csv save_png,
        <DPI>] Choose elements to show on plot. Evts bounded by black triangles.
        option a will show all options (note you still must manually indicate 
        limits/ticks etc if desired. Default is pyplot adaptive
    """
    out=open('readme.txt',w)
    out.write(s)
    out.close()

def set_check_ARGS():
    ap = argparse.ArgumentParser(\
        conflict_handler="resolve",\
        description='To load flags from a file, type @somefile.txt. Use --readme to generate readme.txt for more info. Arguments listed in order of application.',\
        epilog='For more information email rmcassidy@protonmail.com',\
        fromfile_prefix_chars='@')
    ap.add_argument("filename",\
                     help='input filename (comma-separated text, include extension)')
    ap.add_argument("--readme",
                    dest="readme",
                    action="store_true",
                    help="create readme.txt with detailed info on functions")
    ap.add_argument("-o",
                    required=False,
                    metavar="filename",
                    help='output filename (no extension). Default is input filename')
    ap.add_argument("-l","--nolog",
                    dest="l",
                    action="store_true",
                    help="output to terminal instead of .log")
    ap.add_argument("-c",
                    dest="c",
                    metavar="idx",
                    default=[0,1],nargs='+',type=int,
                    help="0-indexed location of data. first is x vals, others are y vals. default is 0 1")
    ap.add_argument("-r",
                    dest="r",
                    metavar="r",
                    default=None,
                    nargs='+',
                    help="0-indexed location of row names and row names to extract. -r [idx] useall to analyze all identified rownames.")
    ap.add_argument("--sh",
                    dest="sh",
                    metavar="lines",
                    default=1,
                    type=int,
                    help="number of lines to skip before reading as data. Default=1. Purpose is to skip non-numerical headers.")
    ap.add_argument("--trim",
                    metavar=['n'],
                    nargs=2,
                    type=float,
                    help="remove n number of samples from front and m from end of all data series.")
    ap.add_argument("--ds",
                    dest="ds",
                    metavar="n",
                    const=2,
                    nargs='?',
                    type=float,
                    help="downsample every n samples. See readme for more info.") 
    ap.add_argument("--fdiv", 
                    metavar='f',
                    nargs='+',
                    type=float,
                    help="divide each column by a factor. single entry divides all data series by that factor")
    ap.add_argument("--rdiv",
                    metavar='c',
                    nargs='?', 
                    const=0,
                    type=str,
                    help="divide all other data series by this reference. If not row, use col_[idxn] e.g. -c 0 1 2 3 --rdiv col_3")
    ap.add_argument("--filt",
                    metavar='option',
                    default=[],
                    nargs='+',
                    type=str,
                    help="inclusive options: [efa,<alpha> lpf,<freq>,<transfreq> hpf,<freq>,<transfreq> bpf,<upperfreq>,<lowerfreq>,<transfreq> brf,<upperfreq>,<lowerfreq>,<transfreq> rmn,<window size> rmd,<window size>]   Smooth data set without calculating events. Note options require a comma with a modifier; do not add any space between option,modifier.")
    ap.add_argument("--norm",
                    metavar='option',
                    default=[],
                    nargs='+',
                    type=str,
                    help="exclusive options: [(mean | med | rmn,<window size> | rmd,<window size> | lsq | lpf,<alpha>)]   Calculate reference (fity), residual (dfy), and proportion residual (dff0)")
    ap.add_argument("--evts",
                    metavar='option',
                    default=[],
                    nargs='+',
                    type=str,
                    help="exclusive options: [(raw | fity | dfy | dff0) (xc,<xval cutoff> | xcs,<sample count cutoff>) (yc,<-yval cutoff>,<+yvalcutoff> | yp,<low proportion cutoff>,<high proportion cutoff> | ystd,<below n std dev cutoff>,<above n std dev cutoff>)]   First parameter: reference line for evt identification. Second parameter: x value cutoff below which not an evt. Third parameter: residual size beyond which considered an evt. Call defaults with 'def'. Defaults are: --evts dfy xc,0 yc,0,0")
    ap.add_argument("--excl",
                    metavar='option',
                    default=[],
                    nargs='+',
                    type=str,
                    help="[(raw | fity | dfy | dff0) (xc,<xval cutoff> | xcs,<sample count cutoff>) (yc,<-yval cutoff>,<+yvalcutoff> | yp,<low proportion cutoff>,<high proportion cutoff> | ystd,<below n std dev cutoff>,<above n std dev cutoff>)]  Removes evts with max amplitude beyond an x or y val threshold (e.g. action potentials in ephys recordings). Does not need to be same units as --evts. Do not enter cutoff if no exclusion on that dimension is desired. Lsq fills in gap in the (post-filtering) raw data. Use --renorm to normalize with different settings and --reevts to identify events with different settings. Call 'same' to use same settings as --norm and --evts")
    ap.add_argument("--renorm",
                    metavar='option',
                    default=[],
                    nargs='+',
                    help="--norm options plus 'same' and (a | above | b | below) for generation of a fitY using a lsq connecting evts above (a) or below (b) the ref line in previous steps. ")
    ap.add_argument("--reevts",
                    metavar='option',
                    default=[],
                    nargs='+',
                    help="--evts options plus 'same'")
    ap.add_argument("--quad",
                    metavar='n',
                    default=[0,0],
                    nargs=2,
                    help="--quad  <x-quad-cutoff>,<y-quad-cutoff> Absolute unit x and y values for sorting evts into quadrants.")
    ap.add_argument("--plot",
                    metavar='option',
                    default=[],
                    nargs='+',
                    type=str,
                    help='inclusive options: [a raw fity dfy dff0 evts excl_evts xlim,<min>,<max> ylim,<min>,<max> xtick,<interval> ytick,<interval> save_csv save_png,<DPI>] Choose elements to show on plot. Evts bounded by black triangles. option a will show all options (note you still must manually indicate limits/ticks etc if desired. Default is pyplot adaptive')
    ap.add_argument("-p",
                    required=False,
                    action="store_true",
                    help='Display pyplot interactive viewer. If --plot not invoked, --plot dfy evts will be used')
    ARGS = ap.parse_args()
    
    # Check/set ARGS
    if len(ARGS.filt)>0: 
        ARGS.filt = [v.split(',') for v in ARGS.filt]
       
    if len(ARGS.norm)>0: 
        ARGS.norm = [v.split(',') for v in ARGS.norm]   
    
    if len(ARGS.evts)>0: 
        if ARGS.evts[0] == 'def': ARGS.evts = ['dfy','xc,0','yc,0,0']
        ARGS.evts = [v.split(',') for v in ARGS.evts]   
    
    if len(ARGS.excl)>0: 
        ARGS.excl = [v.split(',') for v in ARGS.excl]   
    
    if len(ARGS.renorm)>0:
        if ARGS.renorm[0] == 'same': ARGS.renorm = ARGS.norm
        else: ARGS.renorm = [v.split(',') for v in ARGS.renorm]   
    
    if len(ARGS.reevts)>0: 
        if ARGS.reevts[0] == 'same': ARGS.reevts = ARGS.evts
        else: ARGS.reevts = [v.split(',') for v in ARGS.reevts]   
        
    if len(ARGS.plot) !=0 is not None and 'a' in ARGS.plot: 
        ARGS.plot.extend(['raw','fity','dfy','dff0','evts','excl_evts'])
        ARGS.plot = [v.split(',') for v in ARGS.plot]
    
    if ARGS.p and len(ARGS.plot) == 0: ARGS.plot=['dfy','evts']
    
    if ARGS.readme: readme()
    
    return(ARGS)

if __name__ == "__main__":
    global ARGS, LogF
    
    LogF = LogFF()
    ARGS = set_check_ARGS()
    LogF.name(ARGS.o,ARGS.l)
    LogF.logw("arguments:",False)
    LogF.logw(ARGS)
    
    events = False
    
    with PixSpin('Loading data',suppress=ARGS.l):
        LogF.logw('Loading data')
        filename, X, Ydata, names = process_file()
        sps = len(X)/(X[-1]-X[0]) # seconds per sample
        
    with PixSpin('Filtering data',suppress=ARGS.l):
        # Modify whole data set
        if ARGS.trim is None:
            pass
        else:
            LogF.logw("Trim beginning and end of data series")
            X = X[ARGS.trim[0]:ARGS.trim[1]]
            Y_M = []
            for Y in Ydata:
                nY = Y[ARGS.trim[0]:ARGS.trim[1]]
                Y_M.append(np.array(Y))
            Ydata = np.array(Y_M)
            
        if ARGS.r is None or "useall" in ARGS.r or (len(ARGS.r)-1)==len(names): 
            pass
        else:
            LogF.logw("Remove unused rows")
            Y_M = Ydata
            row_names = names
            excluded_row_idx = [i for i,v in enumerate(row_names) if v not in ARGS.r]
            s_a =[]
            for i,c in enumerate(Y_M):
                if i not in excluded_row_idx: s_a.append(c)
            Y_M = np.array(s_a)
            row_names = [row_names[i] for i in range(0,len(row_names)) if i not in excluded_row_idx]
            Ydata = Y_M
            names = row_names
        
        if ARGS.ds is None: 
            pass
        else:
            LogF.logw("Downsample")
            Y_M = Ydata
            M = np.vstack((Y_M,X))
            M = downsample(M)
            Y_M = M[:-1]
            X = np.array(M[-1],dtype=float)
            Ydata = Y_M
            
        if ARGS.fdiv is None: 
            pass
        else:
            LogF.logw('Divide by factor')
            Y_M = Ydata
            if len(ARGS.fdiv)==1: 
                for i in range(0,len(Y_M)): Y_M[i] = Y_M[i]/ARGS.fdiv
            else:
                for i in range(0,len(Y_M)): Y_M[i] = Y_M[i]/ARGS.fdiv[i]
            Ydata = Y_M
        
        if ARGS.rdiv is None: 
            pass
        else:
            LogF.logw('Divide by reference data series')
            Y_M = Ydata
            row_names = names
            idx_ref_c = row_names.index(str(ARGS.rdiv))
            Y_M = np.array([c/Y_M[idx_ref_c] for c in Y_M])
            row_names = np.array(row_names[:idx_ref_c] + row_names[idx_ref_c+1:])
            Ydata = Y_M
            names = row_names
        
        # Create Yseries objects and apply filtering mechanisms to them
        Y_M = [Yseries(Ydata[i],names[i],sps,ARGS.quad) for i in range(0,len(Ydata))]
        
        if len(ARGS.filt)==0:
            pass
        else:
            LogF.logw('Filtering data')
            arg_list = [i for i in ARGS.filt]
            while len(arg_list)>0:
                method,mod,arg_list = return_method(arg_list)
                LogF.logw("filtering method:",False); LogF.logw(method,False)
                LogF.logw("filtering modifier:",False); LogF.logw(mod)    
                for Y in Y_M:
                    if method is 'efa': Y.efa(mod)
                    if method is 'lpf': Y.pass_filter(mod,method)
                    if method is 'hpf': Y.pass_filter(mod,method)
                    if method is 'bpf': Y.pass_filter(mod,method)
                    if method is 'brf': Y.pass_filter(mod,method)
                    if method is 'rmn': Y.run_mean(mod)
                    if method is 'rmd': Y.run_median(mod)
                    Y.reset() # Bubble fitY to Y
                    Y.log(LogF)

    with PixSpin('Normalizing data',suppress=ARGS.l):
        if len(ARGS.norm)==0:
            pass
        else:
            LogF.logw('Normalizing data')
            arg_list = [i for i in ARGS.norm]
            method,mod,arg_list = return_method(arg_list)
            LogF.logw("normalizing method:",False); LogF.logw(method,False)
            LogF.logw("normalizing modifier:",False); LogF.logw(mod)    
            for Y in Y_M:
                if method   is 'efa':   Y.efa(mod)
                elif method is 'lpf':   Y.pass_filter(mod,method)
                elif method is 'hpf':   Y.pass_filter(mod,method)
                elif method is 'bpf':   Y.pass_filter(mod,method)
                elif method is 'brf':   Y.pass_filter(mod,method)
                elif method is 'rmn':   Y.run_mean(mod)
                elif method is 'rmd':   Y.run_median(mod)
                elif method is 'mean':  Y.mean()
                elif method is 'median':Y.median()
                elif method is 'lsq':   Y.lsq_linear(X)
                Y.normalize() # Calculate dfy and dff0 from Y and fitY
                Y.log(LogF)
    
    with PixSpin('Finding events',suppress=ARGS.l):
        if len(ARGS.evts)==0:
            pass
        else:
            events = True
            LogF.logw('Finding events')
            arg_list = [i for i in ARGS.evts]
            for Y in Y_M:
                Coff = return_cutoffs(sps,Y,arg_list,'evts')
                Coff.evaluated = return_evaluated(arg_list)
                Coff.log(LogF)
                Y.CutoffList.append(Coff)
                Y.identify_events(X,'evts')      
                Y.elog(LogF)
                
    with PixSpin('Exclude/Replace',suppress=ARGS.l):
        if len(ARGS.excl)==0:
            pass
        else:
            LogF.logw('Exclude/Replace events')
            arg_list = [i for i in ARGS.excl]
            for Y in Y_M:
                Coff = return_cutoffs(sps,Y,arg_list,'excl')
                Coff.evaluated = return_evaluated(arg_list)
                Coff.log(LogF)
                Y.exclude_replace_events(X,Coff)      
                LogF.logw('Num excluded events:',False); LogF.logw(Y.excluded)
                Y.log(LogF)
                
    with PixSpin('Renormalizing data',suppress=ARGS.l):
        if len(ARGS.renorm)==0:
            pass
        else:
            LogF.logw('Renormalizing data')
            arg_list = [i for i in ARGS.renorm]
            method,mod,arg_list = return_method(arg_list)
            LogF.logw("normalizing method:",False); LogF.logw(method,False)
            LogF.logw("normalizing modifier:",False); LogF.logw(mod)    
            for Y in Y_M:
                if method   is 'efa':   Y.efa(mod)
                elif method is 'lpf':   Y.pass_filter(mod,method)
                elif method is 'hpf':   Y.pass_filter(mod,method)
                elif method is 'bpf':   Y.pass_filter(mod,method)
                elif method is 'brf':   Y.pass_filter(mod,method)
                elif method is 'rmn':   Y.run_mean(mod)
                elif method is 'rmd':   Y.run_median(mod)
                elif method is 'mean':  Y.mean()
                elif method is 'median':Y.median()
                elif method is 'lsq':   Y.lsq_linear(X)
                elif method is 'a':     Y.peakfit('a')
                elif method is 'b':     Y.peakfit('b')
                Y.normalize() # Calculate dfy and dff0 from Y and fitY
                Y.log(LogF)
                
    with PixSpin('Refinding events',suppress=ARGS.l):            
        if len(ARGS.reevts)==0:
            pass
        else:
            events = True
            LogF.logw('Finding events')
            arg_list = [i for i in ARGS.reevts]
            for Y in Y_M:
                Coff = return_cutoffs(sps,Y,arg_list,'reevts')
                Coff.evaluated = return_evaluated(arg_list)
                Coff.log(LogF)
                Y.CutoffList.append(Coff)
                Y.identify_events(X,'reevts')      
                Y.elog(LogF)
    
    with PixSpin('Characterizing events',suppress=ARGS.l):
        if not events:
            pass
        else:
            LogF.logw('Characterizing events')
            for Y in Y_M: Y.characterize_events()
        
    with PixSpin('Printing files',suppress=ARGS.l):    
        LogF.logw('Printing files')
        if len(ARGS.reevts)==0 and len(ARGS.evts)==0:
            pass
        else:
            e_out(X, Y_M, ARGS.o,names)
            e_formatted_out(X, Y_M, ARGS.o,names)
            
    with PixSpin('Making plots',suppress=ARGS.l):
        LogF.logw('Generate plot output')
        if len(ARGS.plot) == 0:
            pass
        else:
            make_plot(X, Y_M, filename,names,ARGS.plot)
    
    LogF.close()
        
    if ARGS.p: 
        with PixSpin('Showing plots'):
            plt.show()        

    
    
    
