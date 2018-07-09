
EVENTS=1000000
nohup python -u csc_daq_rate.py zerobias_306091 -n $EVENTS > logs/zerobias_306091_$EVENTS.log &
nohup python -u csc_daq_rate.py singlemu_306092 -n $EVENTS > logs/singlemu_306092_$EVENTS.log &
nohup python -u csc_daq_rate.py singlemu_306135 -n $EVENTS > logs/singlemu_306135_$EVENTS.log &
nohup python -u csc_daq_rate.py singlemu_306154 -n $EVENTS > logs/singlemu_306154_$EVENTS.log &

EVENTS=25000
nohup python -u csc_daq_rate.py zmu_306091 -n $EVENTS > logs/singlemu_306154_$EVENTS.log &
nohup python -u csc_daq_rate.py zmu_316995 -n $EVENTS > logs/singlemu_306154_$EVENTS.log &
nohup python -u csc_daq_rate.py zmu_317661 -n $EVENTS > logs/singlemu_306154_$EVENTS.log &

tail logs/* -f
