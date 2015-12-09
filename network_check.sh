#!/bin/bash

ROUTER=10.5.5.9
(! ping -c1 $ROUTER > /dev/null 2>&1) &&  ifdown wlan0 > /dev/null 2>&1 && ifup wlan0 > /dev/null 2>&1wq

