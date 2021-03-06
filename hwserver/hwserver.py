#!/usr/bin/python2.6

# Project path
import sys
import re
import os
path = os.path.abspath(re.sub(r'\/[^\/]+$', '', sys.argv[0]))
sys.path.append(path)

from concurrence import dispatch, Tasklet
from homehardware import HomeAutoDispatcher, MicroLANReadROM, HardwareError, MicroLANError, MicroLANListAll, MicroLANConvertTemperature, MicroLANReadTemperature
import logging
from config import *
from hwapi import HomeLogicAPIServer
from concurrence.http import WSGIServer
from homelogic import HomeLogic

def setupLogging():
    log = logging.getLogger("")
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    log.addHandler(ch)

def main():
    try:
        setupLogging()

        dispatcher = HomeAutoDispatcher()
        Tasklet.new(dispatcher.loop)()
        dispatcher.open_ports(
            conf("hardware", "port1", "/dev/ttyS0"),
            conf("hardware", "port2", "/dev/ttyS1")
        )

#        try:
#            print "ReadROM: %s" % dispatcher.request(MicroLANReadROM(0))
#        except MicroLANError as e:
#            print type(e).__name__
#        try:
#            print "SearchROM: %s" % dispatcher.request(MicroLANSearchROM(0, 0, [0, 0, 0, 0, 0, 0, 0, 0]))
#        except MicroLANError as e:
#            print type(e).__name__


        def a():
            while True:
                #for i in xrange(0, 3):
                #    try:
                #        print "Line %d ReadROM: %s" % (i + 1, dispatcher.request(MicroLANReadROM(i)))
                #    except MicroLANError as e:
                #        print "Line %d ReadROM: %s" % (i + 1, type(e).__name__)
                devs = {}
                for i in xrange(0, 3):
                    try:
                        req = MicroLANListAll(dispatcher, i)
                        devices = req.execute()
                    except MicroLANError as e:
                        print "Line %d SearchROM: %s" % (i + 1, type(e).__name__)
                    else:
                        #print "Line %d SearchROM: %s" % (i + 1, devices)
                        if devices:
                            try:
                                dispatcher.request(MicroLANConvertTemperature(i))
                            except MicroLANError as e:
                                print "Line %d ConvertTemperature: %s" % (i + 1, type(e).__name__)
                            else:
                                devs[i] = devices
                Tasklet.sleep(1)
                print "---"
                for i in xrange(0, 3):
                    devices = devs.get(i)
                    if devices:
                        print "Line %d" % (i + 1)
                        for dev in devices:
                            Tasklet.sleep(0.1)
                            try:
                                #print "ReadTemperature of %s: %.1f" % (dev, dispatcher.request(MicroLANReadTemperature(i, dev)))
                                dispatcher.request(MicroLANReadTemperature(i, dev))
                            except MicroLANError as e:
                                print "ReadTemperature of %s: %s" % (dev, type(e).__name__)
                Tasklet.sleep(2)

        def b():
            while True:
                for j in xrange(0, 3):
                    for i in xrange(0, 30):
                        dispatcher.relay_set(i + 1, True)
                        dispatcher.relay_set((i + 15) % 30 + 1, False)
                        Tasklet.sleep(0.05)
                dispatcher.relay_clear_all()
                Tasklet.sleep(1)
                for i in xrange(0, 30):
                    dispatcher.relay_set(i + 1, True)
                    Tasklet.sleep(0.05)
                Tasklet.sleep(1)
                for i in xrange(0, 30):
                    dispatcher.relay_set(i + 1, False)
                    Tasklet.sleep(0.05)
                Tasklet.sleep(1)
                for j in xrange(0, 5):
                    dispatcher.relay_set_all()
                    Tasklet.sleep(0.3)
                    dispatcher.relay_clear_all()
                    Tasklet.sleep(0.3)

        Tasklet.new(a)()
        #Tasklet.new(b)()

        logic = HomeLogic(dispatcher)
        hwapi = HomeLogicAPIServer(dispatcher, logic)
        server = WSGIServer(hwapi)
        addr = conf('hwserver', 'addr', '127.0.0.1')
        port = confInt('hwserver', 'port', 8081)
        server.serve((addr, port))
        logging.getLogger("hwserver").info("Serving API at %s:%s", addr, port)
        while True:
            Tasklet.sleep(100)

    except HardwareError as e:
        print e
        os._exit(1)
    except Exception as e:
        logging.exception(e)
        os._exit(1)

dispatch(main)

