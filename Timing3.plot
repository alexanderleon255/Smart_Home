set output 'Timing3.svg
set terminal svg
set multiplot
set grid
set key tmargin
set title "Clients end date (scheduled -> finished)"
set xlabel "audio cycles"
set ylabel "usec"
plot "profiler.log" using 1 title "Audio period" with lines, "profiler.log" using 8 title "input.jarvis-mic-source/96" with lines, "profiler.log" using 16 title "output.jarvis-mic-source/98" with lines, "profiler.log" using 24 title "alsa_capture.sonobus/93" with lines, "profiler.log" using 32 title "alsa_playback.sonobus/95" with lines, "profiler.log" using 40 title "jarvis-mic-source/33" with lines, "profiler.log" using 48 title "pw-record/39" with lines, "profiler.log" using 56 title "pw-record/122" with lines, "profiler.log" using 64 title "pw-record/130" with lines
unset multiplot
unset output
