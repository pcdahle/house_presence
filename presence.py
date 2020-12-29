import subprocess
import time
import toml

CFGFILE = "presence.cfg"
T_POLL_TIME_S = 5
T_AWAY_UNTIL_CONFIRMED_AWAY_H = 24

def hour_to_sec(hour):
    return 3600 * hour
def sec_to_hour(sec):
    return sec / 3600.0

class Domoticz:
    def __init__(self):
        pass

    def has_departed(self):
        # Either user has pushed the depart button
        # or no interaction with any physcial button in the house for AWAY_UNTIL_CONFIRM time
        return False

    def has_arrived(self):
        # User has pushed some physical button in the house with T_POLL_TIME * 2 period
        return False

    def guess_home(self):
        return True

class PhoneMonitor:
    def __init__(self, PhoneIPs):
        self.ips = PhoneIPs

    def not_present(self):
        return not self.present()

    def present(self):
        n_phones_present = 0
        for ip in self.ips:
            currentstate = subprocess.call('arping -q -c1 -W 1 '+ ip + ' > /dev/null', shell=True)
            if (currentstate == 0):
                n_phones_present += 1
                break
        if (n_phones_present>0):
            self.t_last_present_s = time.time()
            return True
        else:
            return False

    def time_since_last_present_s(self):
        return time.time() - self.t_last_present_s

    def time_since_last_present_h(self):
        return sec_to_hour(self.time_since_last_present_s)


class HouseMachine(StateMachine):
    home = State('Home')
    away = State('Away')

    init_to_home = init.to(home)
    init_to_away = init.to(away)    
    arrive = away.to(home)
    depart = home.to(away)

    def on_arrive(self):
        # TODO: Call Domoticz arrival scene
        pass

    def on_depart(self):
        # TODO: Call Domoticz departure scene
        pass

    @staticmethod
    def find_first_state(self):
        # TODO: determine state
        if Domoticz().guess_home:
            start_state = 'home'
        else:
            start_state = 'away'
        return HouseMachine(start_value=start_state)

house_state = HouseMachine.find_first_state()
phone_monitor = PhoneMonitor("<MAC ADDRESS>")
domoticz = Domoticz()

cfg = toml.load(cfgfile)

while True:
    time.sleep(T_POLL_TIME_S)
    if house_state.is_home:
        if domoticz.has_departed():
            house_state.depart()
        elif phone_monitor.not_present():
            if (phone_monitor.time_since_last_present_min >= T_AWAY_UNTIL_CONFIRMED_TEMPORARY_AWAY_MIN):
                domoticz.empty_house()
            if (phone_monitor.time_since_last_present_h >= T_AWAY_UNTIL_CONFIRMED_AWAY_H):
                house_state.depart()

    elif house_state.is_away:
        if domoticz.has_arrived():
            house_state.arrive()
        elif phone_monitor.present():
            domoticz.arrive()
            house_state.arrive()
        