'''
Created on 11 Aug 2019

@author: marc
'''

state_html = """
  <fieldset>
    <legend>Base Time:</legend>
    <div>Turn
       <input type="radio" id="bt-on-radiobox{0}" name="bt-on-or-off{0}" value="1" checked> ON, or
       <input type="radio" id="bs-off-radiobox{0}" name="bt-on-or-off{0}" value="0"> OFF at
    </div>
    <br>
    <div>
      <input type="radio" id="bt-rel-radiobox{0}" name="base-abs-or-rel{0}" value="abs" checked> Relative:  
      <select id="bt-rel-dd{0}">
         <option value="sr" checked >Sunrise</option>
         <option value="ss">Sunset</option>
      </select>
      <br>
      <input type="radio" id="bt-abs-radiobox{0}" name="base-abs-or-rel{0}" value="rel"> Absolute: <input type="time"  id="bt-abs-ts{0}"  name="base-abs-time{0}" disabled Value="08:30">
      <br>
      <br>
    </div>
    <fieldset>
      <legend><input type="checkbox" id="bt-os-chkbox{0}" name="main-offset-check{0}" value="checked"> Offset:</legend>
        <input type="radio" id="bt-os-plus{0}" name="base-offset-plus-minus{0}" value="plus" checked disabled> +
        <input type="radio" id="bt-os-minus{0}" name="base-offset-plus-minus{0}" value="minus" disabled> -
      &emsp;&emsp;<input type="time" id="bt-os-time{0}" name="base-offset{0}" Value="00:30" disabled>
    </fieldset>
  </fieldset>
  <br>
  
  <fieldset>
    <legend><input type="checkbox" id="ls-chkbox{0}" name="limitation-check{0}" value="checked">Limit Activation</legend>
      Only apply if Base Time occurs
    <input type="radio" id="ls-bfr-radiobox{0}" name="ls-before-or-after{0}" value="before" checked disabled> Before:  
    <input type="radio" id="ls-aft-radiobox{0}" name="ls-before-or-after{0}" value="after" disabled> After:
    <br>
    <br>
    <div>
      <input type="radio" id="ls-rel-radiobox{0}" name="ls-abs-or-rel{0}" value="abs" checked disabled> Relative:  
        <select id="ls-rel-dd{0}" disabled>
          <option value="sr">Sunrise</option>
          <option value="ss">Sunset</option>
      </select><br>
      <input type="radio" id="ls-abs-radiobox{0}" name="ls-abs-or-rel{0}" value="rel"  disabled>Absolute: <input type="time"  id="ls-abs-ts{0}"  name="ls-abs-time{0}" Value="09:30" disabled>
      <br>
      <br>
    </div>
    <fieldset>
      <legend><input type="checkbox" id="ls-os-chkbox{0}" name="ls-offset-check{0}" value="checked"  disabled> Offset:</legend>
        <input type="radio" id="ls-os-plus{0}" name="ls-offset-plus-minus{0}" value="plus" checked disabled> +
        <input type="radio" id="ls-os-minus{0}" name="ls-offset-plus-minus{0}" value="minus" disabled> -
      &emsp;&emsp;<input type="time" id="ls-os-time{0}" name="ls-offset{0}" Value="00:30" disabled>
    </fieldset>
  </fieldset>
"""
state_script = """
var bt_rel_radiobox{0} = document.getElementById('bt-rel-radiobox{0}');
var bt_abs_radiobox{0} = document.getElementById('bt-abs-radiobox{0}');
var bt_rel_dd{0} = document.getElementById('bt-rel-dd{0}');
var bt_abs_ts{0} = document.getElementById('bt-abs-ts{0}');
bt_rel_radiobox{0}.onchange = function() {{
  bt_rel_dd{0}.disabled = !this.checked;
  bt_abs_ts{0}.disabled = this.checked;
}};
bt_abs_radiobox{0}.onchange = function() {{
  bt_rel_dd{0}.disabled = this.checked;
  bt_abs_ts{0}.disabled = !this.checked;
}};

var bt_os_chkbox{0} = document.getElementById('bt-os-chkbox{0}');
var bt_os_plus{0} = document.getElementById('bt-os-plus{0}');
var bt_os_minus{0} = document.getElementById('bt-os-minus{0}');
var bt_os_time{0} = document.getElementById('bt-os-time{0}');
bt_os_chkbox{0}.onchange = function() {{
  bt_os_plus{0}.disabled = !this.checked;
  bt_os_minus{0}.disabled = !this.checked;
  bt_os_time{0}.disabled = !this.checked;
}};

var ls_rel_radiobox{0} = document.getElementById('ls-rel-radiobox{0}');
var ls_abs_radiobox{0} = document.getElementById('ls-abs-radiobox{0}');
var ls_rel_dd{0} = document.getElementById('ls-rel-dd{0}');
var ls_abs_ts{0} = document.getElementById('ls-abs-ts{0}');
ls_rel_radiobox{0}.onchange = function() {{
  ls_rel_dd{0}.disabled = !this.checked;
  ls_abs_ts{0}.disabled = this.checked;
}};
ls_abs_radiobox{0}.onchange = function() {{
  ls_rel_dd{0}.disabled = this.checked;
  ls_abs_ts{0}.disabled = !this.checked;
}};

var ls_os_chkbox{0} = document.getElementById('ls-os-chkbox{0}');
var ls_os_plus{0} = document.getElementById('ls-os-plus{0}');
var ls_os_minus{0} = document.getElementById('ls-os-minus{0}');
var ls_os_time{0} = document.getElementById('ls-os-time{0}');
var ls_chkbox{0} = document.getElementById('ls-chkbox{0}');
var ls_bfr_radbox{0} = document.getElementById('ls-bfr-radiobox{0}');
var ls_aft_radbox{0} = document.getElementById('ls-aft-radiobox{0}');
ls_os_chkbox{0}.onchange = function() {{
  ls_os_plus{0}.disabled = !this.checked;
  ls_os_minus{0}.disabled = !this.checked;
  ls_os_time{0}.disabled = !this.checked;
}};

ls_chkbox{0}.onchange = function() {{
  if (ls_chkbox{0}.checked)
  {{
    ls_os_chkbox{0}.disabled = 0
    ls_bfr_radbox{0}.disabled = 0
    ls_aft_radbox{0}.disabled = 0
    ls_rel_radiobox{0}.disabled = 0
    ls_abs_radiobox{0}.disabled = 0
    ls_rel_dd.disabled{0} = !ls_rel_radiobox{0}.checked
    ls_abs_ts.disabled{0} = !ls_abs_radiobox{0}.checked
    ls_os_plus{0}.disabled = !ls_os_chkbox{0}.checked
    ls_os_minus{0}.disabled = !ls_os_chkbox{0}.checked
    ls_os_time{0}.disabled = !ls_os_chkbox{0}.checked
  }}
  else
  {{
    ls_bfr_radbox{0}.disabled = 1
    ls_aft_radbox{0}.disabled = 1
    ls_rel_radiobox{0}.disabled = 1
    ls_abs_radiobox{0}.disabled = 1
    ls_rel_dd{0}.disabled = 1
    ls_abs_ts{0}.disabled = 1
    ls_os_chkbox{0}.disabled = 1
    ls_os_plus{0}.disabled = 1
    ls_os_minus{0}.disabled = 1
    ls_os_time{0}.disabled = 1
  }}
}};
"""