set output 'Timing2.svg
set terminal svg
set grid
set title "Driver end date (total cycle processing time)"
set xlabel "audio cycles"
set ylabel "usec"
plot  "profiler.log" using 2 title "Driver end date" with lines 
unset output
