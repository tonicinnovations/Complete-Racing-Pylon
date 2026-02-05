# Creating RGB matrix library
# When you link this library with your binary, you need to add -lrt -lm -lpthread
# So
#   -lrgbmatrix
##
OBJECTS=gpio.o led-matrix.o options-initialize.o framebuffer.o \
        thread.o bdf-font.o graphics.o led-matrix-c.o hardware-mapping.o \
        pixel-mapper.o multiplex-mappers.o tile_rotate_v.o tile90ccw.o \
	content-streamer.o

TARGET=librgbmatrix

###
# After you change any of the following DEFINES, make sure to 'make' again.
#
# ###########      NOTE     ###########
# all of these options can now can be set programmatically and
# via command line flags as well. No real need to change them in the Makefile.
# (So be prepared for these to be removed at some point)
###

HARDWARE_DESC?=regular

#DEFINES+=-DINVERSE_RGB_DISPLAY_COLORS
#DEFINES+=-DSHOW_REFRESH_RATE
#DEFINES+=-DRGB_SCAN_INTERLACED=1
#DEFINES+=-DRGB_SLOWDOWN_GPIO=1
#DEFINES+=-DLSB_PWM_NANOSECONDS=130
#DEFINES+=-DDISABLE_HARDWARE_PULSES
#DEFINES+=-DFIXED_FRAME_MICROSECONDS=5000
#DEFINES+=-DDISABLE_BUSY_WAITING
#DEFINES+=-DENABLE_WIDE_GPIO_COMPUTE_MODULE
#HARDWARE_DESC=adafruit-hat-pwm
#DEFINES+=-DONLY_SINGLE_SUB_PANEL

DEFINES+=$(USER_DEFINES)
DEFINES+=-DDEFAULT_HARDWARE='"$(HARDWARE_DESC)"'
INCDIR=../include
CFLAGS=-W -Wall -Wextra -Wno-unused-parameter -O3 -g -fPIC $(DEFINES) -march=native
CXXFLAGS=$(CFLAGS) -fno-exceptions -std=c++11

all : $(TARGET).a $(TARGET).so.1

$(TARGET).a : $(OBJECTS)
	$(AR) rcs $@ $^

$(TARGET).so.1 : $(OBJECTS)
	$(CXX) -shared -Wl,-soname,$@ -o $@ $^ -lpthread  -lrt -lm -lpthread

led-matrix.o: led-matrix.cc $(INCDIR)/led-matrix.h
thread.o : thread.cc $(INCDIR)/thread.h
framebuffer.o: framebuffer.cc framebuffer-internal.h
graphics.o: graphics.cc utf8-internal.h

%.o : %.cc compiler-flags
	$(CXX) -I$(INCDIR) $(CXXFLAGS) -c -o $@ $<

%.o : %.c compiler-flags
	$(CC)  -I$(INCDIR) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJECTS) $(TARGET).a $(TARGET).so.1

compiler-flags: FORCE
	@echo '$(CXX) $(CXXFLAGS)' | cmp -s - $@ || echo '$(CXX) $(CXXFLAGS)' > $@

.PHONY: FORCE
