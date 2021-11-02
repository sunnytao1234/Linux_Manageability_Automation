#! /bin/bash

source /etc/environment
source /etc/profile
export DISPLAY=:0
fsunlock
cd /root

while [ 1 ]
do
	if [ -e $flag_file ]
	then
		resp=`head -1 $flag_file`
		echo $resp>>log.log
		if [[ $resp != 'testing' ]]
		then
			flag=2
			break
		else
			flag=1
		fi
	else
		flag=0
	fi
	echo 'flag'$flag>>log.log
	pid=`ps -ef|grep $exec_file|grep -v grep|grep -v xterm| awk '{print $2}'`
	echo $pid>>log.log
	if [[ $flag -eq 1 && -n $pid ]]
	then
		continue
	else
		sleep 30
		sudo xterm -e $exec_file
	fi
	sleep 3
done
		
		


