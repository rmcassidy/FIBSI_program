Version: FIBSI 1.0.0

# Frequency Independent Biological Signal Identification
-----
FIBSI
Version 1.0.1

By Ryan Michael Cassidy (rmcassidy@pm.me) and Max Odem (Max.Odem@uth.tmc.edu)

This is the program described in the publication:

>Cassidy RM, Bavencoffe AG, Lopez ER, Cheruvu SS, Walters ET, Uribe R, Krachler AM, Odem MA. Electrophysiological and imiaging valdiation of an open-source frequency-independent biological signal identification program (FIBSI) that simplifies intensive analysis of non-stationary time series data. PLoS Computational Biology 2020 XX(XX):XXXX-XXXX doi:XXXX

-----
# Table of Contents

[I Version changes](#i.-version-changes)

[II  Usage](#ii.-usage)

>[FLAGS](#flags)

>[FURTHER EXPLANATION](#further-flag-explanation-and-examples)

[III Program background and conceptual design](#iii.-program-background-and-conceptual-design)

[IV  Prerequisites and installation](#iv.-prerequisites-and-installation)

------
## I. Version changes

This is the original version of the program. See first line for version number. We intend for this program to be developed using SemVer notation https://semver.org/

------
## II. Usage

>`FIBSI.py FILENAME [...options]`

FILENAME refers to the input X-Y data series file. It must be in a comma-separated format and organized such that X and Y data are found in distinct columns. The extension is required within the filename but can be of any type (e.g. file.txt or file.csv)

## FLAGS
Note: flags are listed in order of program processing. In any option where a comma is required, there must be NO space on either side of the comma. In options with multiple commas, if one parameter should remain default, use ''. e.g.  --evts yc,'',20

------

-h  --help
>returns help message

------

-v  --version
>returns version

------

-l  --nolog
>outputs log information to terminal instead of to .log file

------

-o  --output[name]
>name of output file (no extension needed)

------

-c  --columns   [X,y1,y2...]
>0-indexed location of data within input. first is for X, remainder for Y. *default is 0 1*

------

-r  --rows  [idx,n1,n2...]
>0-indexed location of the column containing row names, and the list of rownames to include. If no row names are listed after flag, all rownames will be included. 

------

--sh    [n]
>number of header lines to skip before reading as data. *default = 1*

------

--trim  [m,n]
>number of datapoints to remove from beginning and end of file. m from beginning, n from end.

------

--ds    [n]
>downsampling. keeps every nth sample. *If invoked, default=2*. e.g. n=2, keeps every 2nd sample. If n=0.25, removes every 4th sample. If n=10, keeps every 10th item.

------

--fdiv  [f1,f2...]
>divide all Y values by a single unit factor, or each Y series by its own factor. This will be in the 0-indexed column order of the dataset   (e.g. area of a recording region).

------

--rdiv  [colname]
>divide all other Y values at a given X by this Y series. If using -r, use the same rowname indicated in -r. If not, use the 0-indexed column number like so: col_[idx] (e.g. col_2). This Y series is removed from further analysis.

------

--filt  [OPTIONS...]
>series of options to smooth/filter data prior to beginning of analysis. this step is optional. multiple filters can be applied in the order entered. These are applied to each Y series individually.

--filt  efa,[alpha]
>applies an exponential filter with given alpha. e.g. efa,0.05

--filt  lpf,[Fc],[b]
>applies a low-pass filter with given frequency cutoff (Fc) and transition frequency (b). Blackman window and sinc function. If [b> is not given, calculated as 0.95*Fc.

--filt  hpf,[Fc],[b]
>applies a high-pass filter.

--filt  bpf,[uFc],[lFc],[b]
>applies a band-pass filter with given upper frequency cutoff (uFc) and lower frequency cutoff (lFc) and optional transition frequency (b).

--filt  brf,[uFc],[lFc],[b]
>applies a reverse band-pass filter.

--filt  rmn,[ws]
>applies a running mean filter using a window size (ws) referring to number of samples. For given point Yn, the mean is derived from [Yn-ws/2,...Yn,...Yn+ws/2]. E.g. ws = 6, for Y10, mean is derived for [Y6,...Y10,..Y13]. Odd window sizes/2 are rounded to nearest integer. Start and end points will rely on only right-side or left-side of window for normalization.

--filt  rmd,[ws]
>applies a running median filter.

------

--norm  [OPTION]
>series of options to generate the fitted Y (fitY) series for each Y series using normalizaton procedures. Only one can be used. Residuals are then calculated as dfY = Y-fitY and proportion of referenece df/f0 = dfY/fitY 

--norm  mean
>fitY = mean(Yseries)

--norm  med
>fitY = median(Yseries)

--norm  lsq
>fitY is the result of a least squares (linear) regression.

--norm  efa,[alpha]
>fitY is the result of the exponential filter.

--norm  lpf,[Fc],[b]
>fitY is the result of low-pass filter.

--norm  hpf,[Fc],[b]
>fitY is the result of high-pass filter.

--norm  bpf,[uFc],[lFc],[b]
>fitY is the result of band-pass filter.

--norm  brf,[uFc],[lFc],[b]
>fitY is the result of reverse band-pass filter.

--norm  rmn,[ws]
>fitY is the result of the running mean filter. (see --filt for explanation)

--norm  rmd,[ws]
>fitY is the result of the running median filter.

------

--evts  [OPTIONS...]
>reference line and parameters by which to identify events. 

--evts  def
>calls defaults; --evts def is equivalent to --evts dfy xc,0 yc,0,0

--evts  [REFERENCE]
>select the Y series which is used to identify events with.

--evts  raw
>events are found along the post-filtering, pre-normalization Y series. Unless raw Y series is already centered around y=0, events are not likely to be found.

--evts  fity
>events are found along the reference Y series.

--evts  dfy
>events are found along the residual Y series.

--evts  dff0
>events are found along the residual proportion of reference Y series.

--evts  [PARAMETERS]
>bounding parameters by which events are included into initial tabulation of events.

--evts  xc,[xval]
>events where (Xend - Xstart) < xc are not included. This is in units of X.

--evts  xcs,[n]
>events where (Xn - Xm) < xcs, where n=sample# of end point, and m=sample# of start point, are not included. This is in number of samples.

--evts  yc,[-yvc],[+yvc]
>events with -yvc < amplitude < +yvc are not included. -yvc is the lower cutoff (for belows), and +yvc is the upper cutoff (for aboves). This is in units of yvalue.

--evts  yp,[ylow],[yhigh]
>events with amplitude between the [ylow> quantile or [yhigh> quantile are not included. [ylow> is the lower quantile cutoff and [yhigh> is the upper quantile. This is in % units (e.g. yp,5,95)

--evts  ystd,[ylow],[yhigh]
>events with amplitudes that are not beyond [ylow> number of standard deviations (std) below the mean or [yhigh> number of stds above the mean are not included. This is in rational numbers (e.g. ystd,0.47,2 includes waves with amplitude below 0.47 stds of mean, and 2 stds above the mean)

------

--excl  [OPTIONS...]
>parameters by which to exclude events and the reference line to use to recreate a new Y series

--excl  same
>uses the same parameters as are included in --norm and --events

--excl  [REFERENCE]
>Same options as --evts [(raw fity| dfy | dff0)]. Select Y series which will be used to generate the output Y series after exclusion. 

--excl  [PARAMETERS]
>bounding paramters by which events are EXCLUDED. Same options as --evts, except that these are the boundaries beyond which events are EXCLUDED.

------

--renorm[OPTION]
>all options usable in --norm are usable in --renorm. Parameters for a second round of normalization. This will be applied to the post-filtering, post-exclusion Y series. If no exclusion, applied to post-filtering, pre-normalization Y series. 

--renormsame
>Uses the same option applied to --norm. NOTE 

--renormabove
>(a is also accepted) Peakfitting. Calculates a reference Y series by connecting all of the above amplitudes (peaks). This is especially useful for normalizing event direction to all be in one direction.

--renormbelow
>(b is also accepted) calculates the reference Y from connecting the troughs.

------

--reevts[OPTION]
>Same options as --evts. reference line and parameters by which to identify events on the post-normalization (and/or post-exclusion) Y series.

--reevtssame
>Uses the same options applied to --evts.

------

--quad  [xc,yc]
>optional parameter for labelling events in quadrants. xc refers to the absolute x value cutoff for event duration (dur), yc refers to absolute y value cutoff for event amplitude (amp).

>Quad 1 = dur<xc amp<yc

>Quad 2 = dur>xc amp<yc

>Quad 3 = dur<xc amp>yc

>Quad 4 = dur>xc amp>yc

------

-p  --showplot
>Display pyplot interactive veiwer. If -p is invoked without --plot, will automatically invoke --plot dfy evts.

------

--plot  [OPTIONS...]
>Parameters altering what is displayed on the plot and included in the .csv output file and .png figure.

--plot  save_csv
>Save data selected into a .csv. Will be a separate .csv for each Y dataset

--plot  save_png,[dpi]
>Save the output plot as a .png. *Default DPI is determined by pyplot*

--plot  [DATA]
>Any and all Y series can be plotted. Only this information is included in the output .csv.

--plot  a
>all Y series and events are shown and all event options are shown

--plot  raw
>The post-filtering, post-exclusion Y series will be shown. If no exclusion is applied, this is post-filtering, pre-normalization.

--plot  fity
>The reference Y series calculated in last round of normalization (norm or renorm)

--plot  dfy
>The residual Y series " "

--plot  dff0
>The residual proportion Y series " "

--plot  evts
>Events are displayed and bounded by isosceles triangles. Rightward point triangles are start points, leftward are end points, upward/downward are peak/troughs.

--plot  excl_evts
>Shows the excluded events from --excl

--plot  [PARAMETERS]
>Alter the display of the plot. Default is left up to pyplot adaptive display.

--plot  xlim,[min],[max]
>The boundaries of the x axis.

--plot  ylim,[min],[max]
>The boundaries of the y axis.

--plot  xtick,[interval]
>Intervals of xticks

--plot  ytick,[interval]
>Intervals of yticks

------

------

## FURTHER FLAG EXPLANATION AND EXAMPLES

Consider file.txt with this structure:

|X   |Y   |rowname  |
|:---:|:---:|:---:|
|0   |1   |rowA     |
|0   |12  |rowB     |
|0   |125 |rowC     |
|0   |7743|rowD    |
|1   |1.1 |rowA     |
|1   |7   |rowB     |
|1   |181 |rowC     |
|1   |1811|rowD    |
|2   |0.9 |rowA     |
|2   |1   |rowB     |
|2   |173 |rowC     |
|2   |1885|rowD    |
|3   |0.8 |rowA     |
|3   |4   |rowB     |
|3   |190 |rowC     |
|3   |1062|rowD    |
|4   |1.2 |rowA     |
|4   |19  |rowB     |
|4   |153 |rowC     |
|4   |9406|rowD    |
|5   |1   |rowA     |
|5   |6   |rowB     |
|5   |104 |rowC     |
|5   |1020|rowD    |

-----------

### rows

`FIBSI.py -i input.csv -c 0 1 --rows 0 rowA rowB rowD`

Separates the data for rowA, rowB, rowD into distinct Y series

`X  = [0, 1, 2, 3, 4, 5] # X data`

`Y1 = [1, 1.1, 0.8, 1.2, 1]  # rowA data`

`Y2 = [12, 7, 1, 4, 19, 6]   # rowB data`

`Y3 = [7743, 1811, 1062, 9406, 1020] # rowD data`


rowC excluded - use --rows 0 to include all rows.

-----------

### fdiv

`FIBSI.py -i input.csv -c 0 1 --rows 0 rowA rowB rowD --fdiv 10`

Divides all y values by 100

```
X  = [0, 1, 2, 3, 4, 5] # X data

Y1 = [0.1, 0.11, 0.08, 0.12, 0.1]   # rowA data

Y2 = [1.2, 0.7, 0.1, 0.4, 1.9, 0.6] # rowB data

Y3 = [774.3, 181.1, 106.2, 940.6, 102.0]# rowD data
```

`FIBSI.py -i input.csv -c 0 1 --rows 0 rowA rowB rowD --fdiv 1 10 100`

Divides each Y series by its own factor

```
X  = [0, 1, 2, 3, 4, 5] # X data

Y1 = [1, 1.1, 0.8, 1.2, 1]  # rowA data

Y2 = [1.2, 0.7, 0.1, 0.4, 1.9, 0.6] # rowB data

Y3 = [77.43, 18.11, 10.62, 94.06, 10.20]# rowD data
```

-----------

### rdiv

`FIBSI.py -i input.csv -c 0 1 --rows 0 rowA rowB rowD --rdiv rowA`

Assume that row A contains independent signal recordings intended to normalize signal intensity. The following command divides rowB and rowD by rowA

```
X  = [0, 1, 2, 3, 4, 5] # X data

Y1 = [12, 6.364, 1.25, 3.333, 15.833, 6]  # rowB/rowA data

Y2 = [7743, 1646.364, 1327.5, 7838.333, 1020] # rowD/rowA data

```

-----------

### filt

`FIBSI.py -i input.csv -c 0 1 --rows 0 rowA rowB rowD --filt rmn,3 efa,0.05`

Applies filters sequentially.

Y1 --(rmn,3)--> Y1filt1 --(efa,0.05)--> Y1filt2

Y2 --(rmn,3)--> Y2filt1 --(efa,0.05)--> Y2filt2

Y1filt2 is now considered the 'raw' data (i.e. Y1) for all further normalization steps.

-----------

### norm

`FIBSI.py -i input.csv -c 0 1 --rows 0 rowA rowB rowD --filt lfp,0.005 --norm rmn,6`

Y1 now has fitY1, dfY1, and dff01 associated with it. fitY1 is the product of the running mean with windowsize 5. dfY1 = Y1 - fitY1. dff01 = dfY1/fitY1

-----------

#### running mean normalization example

Consider this dataset that is 0-index (i.e. Y0 = 125, Y1 = 181... etc) and has had `--norm rmn,6` applied to it

```
Y   = [125, 181, 173, 11, 190, 153, 104, 67, 111, 163]

fitY0 = (125+181+173+11)/4  = 122.5

fitY1 = (125+181+173+11+190)/5  = 136

fitY2 = (125+181+173+11+190+153)/6  = 138.8

fitY3 = (125+181+173+11+190+153+104)/7  = 133.8

fitY4 = (181+173+11+190+153+104+67)/7   = 125.6

fitY5 = (173+11+190+153+104+67+111)/7   = 115.6

fitY6 = (11+190+153+104+67+111+163)/7   = 114.1

fitY7 = (190+153+104+67+111+163)/6  = 131.3

fitY8 = (153+104+67+111+163)/5  = 119.6

fitY9 = (104+67+111+163)/4  = 111.25


fitY = [122.5, 136, 138.8, 133.8, 125.6, 115.6, 114.1, 131.3, 119.6, 111.25]

dfY=Y-fitY   = [2.5, 45, 34.2, -122.8, 64.4, 37.4, -10.1, -64.3, -8.6, 51.75]

dff0=dfY/fitY= [0.02, 0.331, 0.246, -0.918, 0.513, 0.324, -0.089, -0.49, -0.072, 0.465]
```

-----------

### evts

`FIBSI.py -i input.csv -c 0 1 --norm rmn,6 --evts def`

NOTE: `--evts def` is equivalent to  `--evts dfy xc,0 yc,0,0` and means that all identifed events will be included for further analysis

The basic algorithic approach is as follows and occurs in a single, ordered read of a Y series from 0 index to end index. Consider the following Y, dfY and fitY series calculated with the command indicated above and dfy calculated in running medean example. 

Consider the data with the following structure:

|  **Index/Xvalue**  |0|1|2|3|4|5|6|7|8|9|
|:----------------:|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|
|y value             |  2.5  |  45  |  34.2  |  -122.8  |  64.4  |  37.4  |  -10.1  |  -64.3  |  -8.6  |  51.75  |

As the program reads from left to right on the y-value line, it takes the following steps

**Step 1:**
idx = 0
Not in above event
Not in below event
Item at index 0 is >0
Set 'above' to true
Add item to new event, 'above1'.

**Step 2:**
idx += 1
In above event
Not in below events
Item at index 1 is >0
Above is true
Add to currently opened event, 'above1'

**Step 3:**
idx += 1
In above event
Not in below event
Item at index 2 is >0
Above is true
Add to currently opened event, 'above1'

**Step 4:**
idx += 1
In above event
Not in below event
Item at index 3 is <=0:
Set below to true
Above is true; set above to false and close 'above1'
Add to new event, 'below1'

**Step 5:**
idx += 1
Not in above event
In below event
Item at index 4 is >0:
Set above to true
Below is true; set below to false and close 'below1'
Add to new event, 'above2'

**Step 6:**
idx += 1
In above event
Not in below event
Item at index 5 is >0:
Above is true
Add to currently opened event, 'above2'

**Step 7:**
idx += 1
In above event
Not in below event
Item at index 6 is <=0:
Set below to true
Above is true; set above to false and close 'above2'
Add to new event, 'below2'

**Step 8:**
idx += 1
Not in above event
In below event
Item at index 7 is <=0:
Below is true
Add to currently opened event, 'below2'

**Step 9:**
idx += 1
Not in above event
In below event
Item at index 8 is <=0:
Below is true
Add to currently opened event, 'below2'

**Step 10:**
idx += 1
Not in above event
In below event
Item at index 9 is >0:
Set above to true
Below is true; set below to false and close 'below2'
Add to new event, 'above3'

**Step 11:**
idx += 1
In above event
Not in below event
Reached end of list, close currently open event, 'above3'

List of events with amplitude bolded:

|event|v1|v2|v3|
|:---:|:-|:-|:-|
|above1|2.5|**45**|34.2|
|above2|**64.4**|37.4||
|above3|**51.75**|||
|below1|**-122.8**|||
|below2|-10.1|**-64.3**|-8.6|


Event parameters can then be applied to remove events, such as `--evts dfy yc,-50,50`; this command removes above1 from the list of events.

-----------

### excl

`FIBSI.py -i input.csv -c 0 1 --norm rmn,6 --evts def --excl dfy yc,-100,100`

Continuing with the event set described above, the --excl flag removes events that exceed the input parameters, and rebuilds a Y series using the indicated Y series from before. In this case, below1 will be removed; the change in line looks like this:

```
dfy = [2.5, 45, 34.2, -122.8, 64.4, 37.4, -10.1, -64.3, -8.6, 51.75]

excl = [2.5, 45, 34.2, X , 64.4, 37.4, -10.1, -64.3, -8.6, 51.75]
```

X is then calculated by calculating the slope of the line connecting the end point of the previous event (34.2) and the start point of the next event (64.4) via Y2-Y1/(X2-X1), then calculating the value at that time. Here, this (64.4-34.2)/(4-2) with indices substituting as X values; the slope is 15.1. So, X = 45.3

The output Y is now set to:

`Y = [2.5, 45, 34.2, 45.3   , 64.4, 37.4, -10.1, -64.3, -8.6, 51.75]`

-----------

### renorm

Same general application as norm, with the addition of peak-fitting.

-----------

### reevt

Same general application as evts.

-----------

-----------

-----------

## III. Program background and conceptual design

### PROGRAM BACKGROUND

FIBSI is a generalization and extension of the method described in this publication by the authors:

>Odem MA, Bavencoffe AG, Cassidy RM, Lopez ER, Tian JB, Dessauer CW, Walters ET. Isolated nociceptors reveal multiple specializations for generating irregular ongoing activity associated with ongoing pain. Pain 2018 159(11):2347-2362 doi:10.1097/j.pain.0000000000001341

This program was developed to address the need for a signal analysis tool that can detect significant phenomena in time series data while handling these properties common to many biological signals:

1. The pattern generator underlying these phenomena is not known, or may not be distinguishable from noise in the frequency domain.

   *For example, in Odem 2018, we demonstrated that irregular action potential (AP) firing was a common feature of chronic pain nociceptor phenotypes. Our hypothesis is that the generator driving it is inherently stochastic so as to avoid central nervous system filtering.

2. Sampling period is generally short because of the fragile nature of many biological signals

   *For example, patch-clamp electrophysiology setups are stable for only a few minutes. When analyzing AP frequency, a 2hz firing rate produces only 4 APs in a 2 minute recording.

3. Sampling is conducted in low signal strength, high noise environments.

   *For example, in Odem 2018, the subthreshold fluctuations deviated from resting membrane potential by 1.5-3mV, whereas the traditional signal analyzed from neurons in patch-clamp, the AP, is 50mV+ in deviation.

4. Many biological data are shaped by factors proximate-in-time to the signal, then by long-term factors

   *For example, an AP is triggered by an immediately preceding increase in membrane potential on the order of milliseconds; the likelihood of triggering is set by protein expression and electrolyte balance set by the neuron on the order of hours to days

5. The shape of the biological signal's deviation from baseline is often as informative as the frequency.

   *For example, APs are often characterized by their threshold (where the rate of deviation increases substantially, though part of the same waveform), amplitude, duration, and afterhyperpolarization waveform, not just their frequency.

FIBSI addresses these issues by extending the conceptual approach pioneered by the Ramer-Douglas-Peucker algorithim for identifying significant shapes while reducing the total number of points needed to represent said shape. 

### PROGRAM CONCEPTUAL DESIGN

The core FIBSI algorithm performs these steps. 

1. A reference X-Y series is calculated from the data X-Y series (time-series data) in the normalization step. A variety of functions can be applied to generate this reference line, such as a running mean, linear regression, median, etc. This reference line is referred to as fitY (for fitted Y series)

2. The residual difference between the Y series and the fitY series is calculated by Y-fitY, producing dfY (difference Y).

3. (A) Events (i.e. signals) are identifed iteratively by reading across the X-dfY series from x=start to x=end. The start of an 'above' event is identified when the first Y value is encountered that has a value >=0. Each subsequent Y value that remains above 0 is considered part of the 'above' event. The end of the 'above' event is identified when the first Y value below 0 is encountered. The Y value one point previously (x-1) is set as the end point of that 'above' event. The inverse ruleset applies for 'below' events.

4. In some situations, the event information can be used to recalculate the reference line. For example, in Odem 2018, the first 'round' of event identification was used to identify APs, then to remove the X-Y data that corresponded to an AP from the raw dataset, and finally to run a second 'round' of event identification on the modified X-Y data. This removed the influence of APs on functions like the running median, that depend highly on local environment, for the purpose of analyzing the subthreshold fluctuations that produce APs.

   *A reference line can also be calculated based off of the peaks of 'above' events (or troughts of 'below' events).

5. Various properties about the events can then be calculated and output in a variety of ways.

------
## IV. Prerequisites and installation

### FILE LIST

FIBSI.py        All functions needed to run analysis are contained within FIBSI.py

README.md       This file

tutorial.ppt    An instructional powerpoint describing use cases and examples

data.txt        An example data set, collected from XXXX, for use with the tutorial

### PREREQUISITES

FIBSI was written using the Anaconda 1.7 distribution of Python 3. It was developed and tested on several Linux distributions and on Windows 10. It can be run on any system that can run the python 3 interpreter.

The following non-core python 3 packages are required:

-matplotlib
-numpy

### INSTALLATION

-Visit https://www.anaconda.com/ and select the version appropriate for your operating system
-Download FIBSI.py
-Run FIBSI.py by invoking the python interpreter from the command line interface and running it on FIBSI.py. For easiest use, place FIBSI.py directly into the folder with data to analyze


































