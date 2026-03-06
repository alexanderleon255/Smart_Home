set output 'Timing5.svg
set terminal svg
set multiplot
set grid
set key tmargin
set title "Clients duration (active -> finished)"
set xlabel "audio cycles"
set ylabel "usec"
plot "profiler.log" using 10 title "input.jarvis-mic-source/96" with lines, "profiler.log" using 18 title "output.jarvis-mic-source/98" with lines, "profiler.log" using 26 title "alsa_capture.sonobus/93" with lines, "profiler.log" using 34 title "alsa_playback.sonobus/95" with lines, "profiler.log" using 42 title "jarvis-mic-source/33" with lines, "profiler.log" using 50 title "pw-record/39" with lines, "profiler.log" using 58 title "pw-record/122" with lines, "profiler.log" using 66 title "pw-record/130" with lines
unset multiplot
unset output
