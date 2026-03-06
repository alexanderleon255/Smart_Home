set output 'Timing4.svg
set terminal svg
set multiplot
set grid
set key tmargin
set title "Clients scheduling latency (scheduled -> active)"
set xlabel "audio cycles"
set ylabel "usec"
plot "profiler.log" using 9 title "input.jarvis-mic-source/96" with lines, "profiler.log" using 17 title "output.jarvis-mic-source/98" with lines, "profiler.log" using 25 title "alsa_capture.sonobus/93" with lines, "profiler.log" using 33 title "alsa_playback.sonobus/95" with lines, "profiler.log" using 41 title "jarvis-mic-source/33" with lines, "profiler.log" using 49 title "pw-record/39" with lines, "profiler.log" using 57 title "pw-record/122" with lines, "profiler.log" using 65 title "pw-record/130" with lines
unset multiplot
unset output
