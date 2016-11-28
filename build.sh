
cython --embed -o go.c go_gui.py
gcc -Os -I /usr/include/python2.7 -o go go.c -lpython2.7 -lpthread -lm -lutil -ldl
