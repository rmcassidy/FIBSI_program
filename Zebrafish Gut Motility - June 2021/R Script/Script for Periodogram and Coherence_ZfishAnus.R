#Library
library(TSA)
library(seewave)

#read raw and dfy
data = read.csv("AB_7dpf_fedeggyolk2days_hindgut20X_G008_Anus_plot_10A.csv") #Replace Fish ID and ROI#
raw <- data$raw
dfy <- data$dfY

#Verify plots
plot(raw, type = "l", lty = 1, lwd = 1, col = "red")
plot(dfy, type = "l", lty = 1, lwd = 1, col = "red")

#Run FFT
p_raw = periodogram(raw)
p_raw
p_dfy = periodogram(dfy)
p_dfy

#Output Top 1000 Results (raw and dfy)
dd_raw = data.frame(freq=p_raw$freq, spec=p_raw$spec)
order = dd_raw[order(-dd_raw$spec),]
top1000_raw = head(order, 1000) #Specify top number of results
write.csv(top1000_raw, "C:\\R\\AB_7dpf_fedeggyolk2days_hindgut20X_G008_Anus_ROI10rawFFT.csv") #Replace Fish ID and ROI#

dd_dfy = data.frame(freq=p_dfy$freq, spec=p_dfy$spec)
order = dd_dfy[order(-dd_dfy$spec),]
top1000_dfy = head(order, 1000) #Specify top number of results
write.csv(top1000_dfy, "C:\\R\\AB_7dpf_fedeggyolk2days_hindgut20X_G008_Anus_ROI10dfyFFT.csv") #Replace Fish ID and ROI#

#Results output in normalized range 0.0-0.5 (0.5 being the Nyquist frequency)
#Frequency = normalized frequency*sampling rate in Hz (around 0.5-0.8 s per frame depending on the fish, so 1.25-2 Hz)

#Run Coherence
wave1 <- raw
wave2 <- dfy
coh(wave1, wave2, f = 1.610, channel=c(1,1), plot = TRUE, type = "l") #f is the frequency in Hz (frames/s), plots in kHz
coh_results <- coh(wave1, wave2, f = 1.768, plot = FALSE)
write.csv(coh_results, "C:\\R\\AB_7dpf_fedeggyolk2days_hindgut20X_G008_Anus_ROI10coherence.csv") #Replace Fish ID and ROI#

