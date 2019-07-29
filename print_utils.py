'''
Created on 10 May 2019

@author: root
'''
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont

#from relay import relay_process
from status import PowerStatus
#from config import Board
from control import Control
#from boards.SimBoard import SimBoard
from time_utils import calc_and_activate_test_time
from Sun import get_sun

#import cProfile

def daterange(d1, d2):
    return (d1 + timedelta(days=i) for i in range((d2 - d1).days + 1))


def print_day(date, config, status, socket_name, step=10):
    start_date = date - timedelta(days = 1)
    end_date = date + timedelta(days = 1)

    return print_days(start_date, end_date, config, status, socket_name, step)

def get_on_off_times(start_date, end_date, config, socket_name):
    # get a list of times and on/off transition
    transition_seq = []
    sr_ss_seq = []
    socket_cfg = config.sockets[socket_name]
    power = PowerStatus.PWR_UNK

    for d in daterange(start_date, end_date):
        sun = get_sun()
        sunset_lcl = sun.getSunsetTimeLocal(d)
        sunset_utc = sun.getSunsetTimeUtc(d)
        #sunrise_lcl = ConvertUtcToLocalTime(sunrise['dt'])
        sunrise_lcl = sun.getSunriseTimeLocal(d)
        sunrise_utc = sun.getSunriseTimeUtc(d)
        #sunset_lcl = ConvertUtcToLocalTime(sunset['dt'])
        sr_ss_seq.append((sunrise_lcl, sunset_lcl))

        # Calc the auto-values, ignoring override states
        socket_cfg.reset_state_activation_time()
        socket_cfg.calc_activate_times_for_states(d)
        record_for_today = False
        for state in socket_cfg.states:
            activation_time = state.activation_time.activation_time_lcl
            # if activation_time is None, then this state is not active
            if (activation_time):
                record_for_today = True
                power = state.power_state
                transition_seq.append((activation_time, power))

        if record_for_today == False:
            # ie, no transistions occured today, then we need to create a record to mark
            # the current power at the start of the day
            marker_time = d.replace(hour=0, minute=0, second=0, microsecond=0)
            transition_seq.append((marker_time, power))

    transition_seq_ordered = []

    return transition_seq, sr_ss_seq

def print_days(start_date, end_date, config, _status, socket_name, step=10):
    transition_seq, _ss_sr_seq = get_on_off_times(start_date, end_date, config, socket_name)

    # config for printout
    mins_in_day = 60 * 24
    day_width = mins_in_day / step
    last_width_pos = 0
    ON_CHAR = "X"
    OFF_CHAR = "-"

    day_list = []

    # convert list of times into a string
    start_display = False
    last_datetime = None
    last_power_state = PowerStatus.PWR_OFF
    day_map = []
    auto_map = []
    for (act_time, power) in transition_seq:
        if last_datetime is None:
            last_datetime = act_time
            continue

        # see if we/ve gone over a midnight border
        if last_datetime.hour > act_time.hour:
            if start_display:
                # fill in to end of day
                for _ind in range(last_width_pos, day_width):
                    if last_power_state == PowerStatus.PWR_OFF:
                        day_list.append(OFF_CHAR)
                    else:
                        day_list.append(ON_CHAR)

                day_map = ''.join(day_list)
                auto_map.append(''.join(day_map))

                # reset to start of day
                last_width_pos = 0
                day_list = []

            else:
                start_display = True

        if start_display:
            minutes_so_far_today = day_minutes(act_time)
            percentage_of_day = (minutes_so_far_today / (float(mins_in_day)))
            current_width = int(day_width * percentage_of_day)
            for _ind in range(last_width_pos, current_width):
                if last_power_state == PowerStatus.PWR_OFF:
                    day_list.append(OFF_CHAR)
                else:
                    day_list.append(ON_CHAR)

            last_width_pos = current_width

        last_power_state = power
        last_datetime = act_time

    return auto_map

def print_day_image(fn, date, config, socket_name, image_width=800, day_height=5):
    return print_days_image(fn, date, date, config, socket_name, image_width, day_height=3)

def print_days_image(fn, start_date, end_date, config, socket_name, image_width=800, day_height=5, current_day=None):
    # start/finish one day before/efter the required time frame
    # We do not print the img_start_date, but collect info on it so we know the starting
    # power for the 'real' start_date
    img_start_date = start_date - timedelta(days = 1)
    img_end_date = end_date + timedelta(days = 1)

    transition_seq, ss_sr_seq = get_on_off_times(img_start_date, img_end_date, config, socket_name)

    ON_COLOR = 'yellow'
    OFF_COLOR1 = 'white'
    OFF_COLOR2 = 'grey'
    draw_sr_ss = True
    draw_hours = 2
    SUN_COLOR = 'red'
    ss_sr_width = 2
    hour_width = 1
    MINS_IN_DAY = 60 * 24
    HOUR_COLOR = 'black'

    # create image:
    offset_x = 10
    offset_y = 20
    offset_text_x = -10
    num_days = (end_date - start_date).days + 1
    image_hieght = num_days * day_height + offset_y
    img = Image.new('RGB', (image_width, image_hieght), color = OFF_COLOR1)
    day_width = (image_width - (2 *offset_x))

    # build up the image day-by-day
    draw = ImageDraw.Draw(img)
    start_display = False
    last_datetime = None
    last_power_state = PowerStatus.PWR_OFF
    last_x_pos = 0
    day_idx = 0
    today_idx = -1
    sr_ss_idx = 0
    month_count = 0
    month_names = []
    for (act_time, power) in transition_seq:
        if last_datetime is None:
            last_datetime = act_time
            continue

        # see if we/ve gone over a midnight border
        if ((last_datetime.month == act_time.month) and (last_datetime.day < act_time.day)) \
         or ((last_datetime.month < act_time.month) and (act_time.day == 1)) \
         or ((last_datetime.year < act_time.year) and (act_time.month == 1)):

            # see if this the current day for highlighting later:
            if current_day and \
                ((current_day.day == act_time.day) and
                 (current_day.month == act_time.month) and
                 (current_day.year == act_time.year)):
                today_idx = day_idx

            if start_display:
                # draw every other month a slightly different color
                if ((last_datetime.month < act_time.month) and (act_time.day == 1)) \
                 or ((last_datetime.year < act_time.year) and (act_time.month == 1)):
                    rect_x1 = 0
                    rect_x2 = image_width
                    import calendar
                    num_days_in_month = calendar.monthrange(act_time.year, act_time.month)[1]
                    day_idx_mod = day_idx + num_days_in_month
                    if day_idx_mod > num_days:
                        day_idx_mod = num_days
                    rect_y1 = offset_y + ((day_idx + 1) * day_height)
                    rect_y2 = offset_y + ((day_idx_mod) * day_height)
                    rect_xy1 = (rect_x1, rect_y1)
                    rect_xy2 = (rect_x2, rect_y2)
                    if month_count % 2 == 0:
                        draw.rectangle((rect_xy1, rect_xy2), fill=OFF_COLOR2)

                    point_xy_text = (0, rect_y1)
                    month_names.append((point_xy_text, calendar.month_name[act_time.month]))
                    month_count += 1

                # fill in to end of day if PWR is ON
                if last_power_state == PowerStatus.PWR_ON:
                    rect_x1 = last_x_pos
                    rect_x2 = image_width - offset_x
                    rect_y1 = offset_y + (day_idx * day_height)
                    rect_y2 = offset_y + ((day_idx + 1) * day_height)
                    rect_xy1 = (rect_x1, rect_y1)
                    rect_xy2 = (rect_x2, rect_y2)
                    draw.rectangle((rect_xy1, rect_xy2), fill=ON_COLOR)

                # draw on the sr/ss marker desired
                if draw_sr_ss:
                    sr_ss_times = ss_sr_seq[sr_ss_idx]
                    sr_dt = sr_ss_times[0]
                    ss_dt = sr_ss_times[1]
                    # Sunrise
                    minutes_so_far_today = day_minutes(sr_dt)
                    percentage_of_day = (minutes_so_far_today / (float(MINS_IN_DAY)))
                    current_width = int(day_width * percentage_of_day)
                    p_x = current_width + offset_x
                    p_y1 = offset_y + (day_idx * day_height)
                    p_y2 = offset_y + ((day_idx + 1) * day_height)
                    point_xy1 = (p_x, p_y1)
                    point_xy2 = (p_x, p_y2)
                    draw.line((point_xy1, point_xy2), SUN_COLOR, ss_sr_width)
                    # Sunset
                    minutes_so_far_today = day_minutes(ss_dt)
                    percentage_of_day = (minutes_so_far_today / (float(MINS_IN_DAY)))
                    current_width = int(day_width * percentage_of_day)
                    p_x = current_width + offset_x
                    p_y1 = offset_y + (day_idx * day_height)
                    p_y2 = offset_y + ((day_idx + 1) * day_height)
                    point_xy1 = (p_x, p_y1)
                    point_xy2 = (p_x, p_y2)
                    draw.line((point_xy1, point_xy2), SUN_COLOR, ss_sr_width)

                # reset to start of day
                last_x_pos = offset_x
                day_idx += 1

            else:
                start_display = True

            # increment the sunrise/set counter to keep in step with the
            # sequence on-off profile
            sr_ss_idx += 1

        # see if we're on the last day, in whic case we exit the loop
        if day_idx >= num_days:
            # we've collected all the days we're interested in, so exit
            break

        if start_display:
            if act_time > last_datetime:
                minutes_so_far_today = day_minutes(act_time)
                percentage_of_day = (minutes_so_far_today / (float(MINS_IN_DAY)))
                current_width = int(day_width * percentage_of_day)
                if last_power_state == PowerStatus.PWR_ON:
                    rect_x1 = last_x_pos
                    rect_x2 = current_width + offset_x
                    rect_y1 = offset_y + (day_idx * day_height)
                    rect_y2 = offset_y + ((day_idx + 1) * day_height)
                    rect_xy1 = (rect_x1, rect_y1)
                    rect_xy2 = (rect_x2, rect_y2)
                    draw.rectangle((rect_xy1, rect_xy2), fill=ON_COLOR)

                last_x_pos = offset_x + current_width + 1

            last_power_state = power
            last_datetime = act_time

    # draw hour markers as desired
    if draw_hours:
        # get a font
        fnt = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 18)
        # get a drawing context
        for hour in range(0, 24 +1, draw_hours):
            percentage_of_day = (hour / (float(24)))
            current_width = int(day_width * percentage_of_day)
            if current_width >= day_width:
                # shrink by enough pixels to draw the final line.
                current_width = day_width - hour_width
            p_x = current_width + offset_x
            p_y1 = offset_y
            p_y2 = offset_y + num_days * day_height
            point_xy1 = (p_x, p_y1)
            point_xy_text = (p_x + offset_text_x, 0)
            point_xy2 = (p_x, p_y2)
            draw.line((point_xy1, point_xy2), HOUR_COLOR, hour_width)
            draw.text(point_xy_text, str(hour), font=fnt, fill=(0,0,0,255))

    # draw the month names
    fnt = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 12)
    for (point, name) in month_names:
        draw.text(point, name, font=fnt, fill=(0,0,0,255))

    # draw current day marker as desired
    if current_day:
        p_x1 = 0
        p_x2 = image_width - 1
        p_y1 = (offset_y + (today_idx * day_height)) - 1
        p_y2 = (offset_y + ((today_idx + 1) * day_height)) + 1
        point_xy1 = (p_x1, p_y1)
        point_xy2 = (p_x2, p_y2)
        draw.rectangle((point_xy1, point_xy2), outline=HOUR_COLOR)
        # get a font
        fnt = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 12)
        today_text_x = image_width - 50
        point_xy_text = (today_text_x, p_y2)
        draw.text(point_xy_text, "today", font=fnt, fill=(0,0,0,255))

    # draw current time marker as desired
    if current_day:
        minutes_so_far_today = day_minutes(current_day)
        percentage_of_day = (minutes_so_far_today / (float(MINS_IN_DAY)))
        current_width = int(day_width * percentage_of_day)
        line_x1 = current_width + offset_x - 2
        line_x2 = current_width + offset_x + 2
        line_y1 = offset_y
        line_y2 = offset_y + (num_days * day_height)
        rect_xy1 = (line_x1, line_y1)
        rect_xy2 = (line_x2, line_y2)
        draw.rectangle((rect_xy1, rect_xy2), outline=HOUR_COLOR)

    img.save(fn, 'png')


def day_seconds(timenow):
    midnight = timenow.replace(hour=0, minute=0, second=0, microsecond=0)
    return (timenow - midnight).seconds
#    dst_diff = timenow.dst()
#    timenow_dst = timenow + dst_diff
#    return (timenow_dst - midnight).seconds


def day_minutes(timenow):
    seconds = day_seconds(timenow)
    return seconds / 60


def print_days2(relay_process, start_date, end_date, config, status, socket_name, step=10):
    days = []
    count = 0
    for d in daterange(start_date, end_date):
        day_str,_ovr = print_day(relay_process, d, config, status, socket_name, step)
        days.append(day_str)
        count += 1
        #print("{}: {}".format (d.strftime('%Y.%m.%d'), day_str))
    return days

