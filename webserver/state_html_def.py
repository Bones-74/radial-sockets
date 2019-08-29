'''
Created on 11 Aug 2019

@author: marc
'''

state_html = """
<div id="tab_content_{id}" class="tabcontent">
  <input type="checkbox" id="state-active{id}" name="state-active{id}" checked> Use this state
  <input type="number" id="idx{id}" name="index{id}" val="-1">  index
  <fieldset>
    <legend>Base Time:</legend>
    <div>Turn
       <input type="radio" id="bt-on-radiobox{id}" name="bt-on-or-off{id}" value="1" {bt_ON}> ON, or
       <input type="radio" id="bs-off-radiobox{id}" name="bt-on-or-off{id}" value="0" {bt_OFF}> OFF at
    </div>
    <br>
    <div>
      <input type="radio" id="bt-rel-radiobox{id}" name="base-abs-or-rel{id}" value="rel" {bt_REL}> Relative:  
      <select id="bt-rel-dd{id}" name="bt-rel-type{id}" >
         <option value="sr" {bt_REL_SR}>Sunrise</option>
         <option value="ss" {bt_REL_SS}>Sunset</option>
      </select>
      <br>
      <input type="radio" id="bt-abs-radiobox{id}" name="base-abs-or-rel{id}" value="abs" {bt_ABS}> Absolute: <input type="time"  id="bt-abs-ts{id}"  name="base-abs-time{id}" Value="{bt_ABS_time}">
      <br>
      <br>
    </div>
    <fieldset>
      <legend><input type="checkbox" id="bt-os-chkbox{id}" name="main-offset-check{id}" {bt_OS_EN}> Offset:</legend>
        <input type="radio" id="bt-os-plus{id}" name="base-offset-plus-minus{id}" value="plus" {bt_OS_plus} > +
        <input type="radio" id="bt-os-minus{id}" name="base-offset-plus-minus{id}" value="minus" {bt_OS_minus}> -
      &emsp;&emsp;<input type="time" id="bt-os-time{id}" name="base-offset{id}" Value="{bt_OS_time}">
    </fieldset>
  </fieldset>
  <br>

  <fieldset>
    <legend><input type="checkbox" id="ls-chkbox{id}" name="limitation-check{id}" {lim_ACT_EN}>Limit Activation</legend>
      Only apply if Base Time occurs
    <input type="radio" id="ls-bfr-radiobox{id}" name="ls-before-or-after{id}" value="before" {lim_BFR} > Before:  
    <input type="radio" id="ls-aft-radiobox{id}" name="ls-before-or-after{id}" value="after" {lim_AFT} > After:
    <br>
    <br>
    <div>
      <input type="radio" id="ls-rel-radiobox{id}" name="ls-abs-or-rel{id}" value="rel"  {lim_REL}> Relative:  
        <select id="ls-rel-dd{id}" name="ls-rel-type{id}" >
          <option value="sr" {lim_REL_SR}>Sunrise</option>
          <option value="ss" {lim_REL_SS}>Sunset</option>
      </select><br>
      <input type="radio" id="ls-abs-radiobox{id}" name="ls-abs-or-rel{id}" value="abs" {lim_ABS} >Absolute: <input type="time"  id="ls-abs-ts{id}"  name="ls-abs-time{id}" Value="{lim_ABS_time}" >
      <br>
      <br>
    </div>
    <fieldset>
      <legend><input type="checkbox" id="ls-os-chkbox{id}" name="ls-offset-check{id}" {lim_OS_EN} > Offset:</legend>
        <input type="radio" id="ls-os-plus{id}" name="ls-offset-plus-minus{id}" value="plus" {lim_OS_plus}> +
        <input type="radio" id="ls-os-minus{id}" name="ls-offset-plus-minus{id}" value="minus" {lim_OS_minus}> -
      &emsp;&emsp;<input type="time" id="ls-os-time{id}" name="ls-offset{id}" Value="{lim_OS_time}" >
    </fieldset>
  </fieldset>
</div>
"""

state_script = """
var tb_state_active{0} = document.getElementById('tb-state-active{0}');
var state_active{0} = document.getElementById('state-active{0}');
var bt_on_radiobox{0} = document.getElementById('bt-on-radiobox{0}');
var bt_off_radiobox{0} = document.getElementById('bs-off-radiobox{0}');
var bt_rel_radiobox{0} = document.getElementById('bt-rel-radiobox{0}');
var bt_abs_radiobox{0} = document.getElementById('bt-abs-radiobox{0}');
var bt_rel_dd{0} = document.getElementById('bt-rel-dd{0}');
var bt_abs_ts{0} = document.getElementById('bt-abs-ts{0}');
var bt_os_chkbox{0} = document.getElementById('bt-os-chkbox{0}');
var bt_os_plus{0} = document.getElementById('bt-os-plus{0}');
var bt_os_minus{0} = document.getElementById('bt-os-minus{0}');
var bt_os_time{0} = document.getElementById('bt-os-time{0}');
var ls_rel_radiobox{0} = document.getElementById('ls-rel-radiobox{0}');
var ls_abs_radiobox{0} = document.getElementById('ls-abs-radiobox{0}');
var ls_rel_dd{0} = document.getElementById('ls-rel-dd{0}');
var ls_abs_ts{0} = document.getElementById('ls-abs-ts{0}');
var ls_os_chkbox{0} = document.getElementById('ls-os-chkbox{0}');
var ls_os_plus{0} = document.getElementById('ls-os-plus{0}');
var ls_os_minus{0} = document.getElementById('ls-os-minus{0}');
var ls_os_time{0} = document.getElementById('ls-os-time{0}');
var ls_chkbox{0} = document.getElementById('ls-chkbox{0}');
var ls_bfr_radiobox{0} = document.getElementById('ls-bfr-radiobox{0}');
var ls_aft_radiobox{0} = document.getElementById('ls-aft-radiobox{0}');

function bt_rel_radiobox{0}_onchange () {{
  bt_rel_dd{0}.disabled = !bt_rel_radiobox{0}.checked;
  bt_abs_ts{0}.disabled = bt_rel_radiobox{0}.checked;
}}
function bt_abs_radiobox{0}_onchange () {{
  bt_rel_dd{0}.disabled = bt_abs_radiobox{0}.checked;
  bt_abs_ts{0}.disabled = !bt_abs_radiobox{0}.checked;
}}

function bt_os_chkbox{0}_onchange () {{
  bt_os_plus{0}.disabled = !bt_os_chkbox{0}.checked;
  bt_os_minus{0}.disabled = !bt_os_chkbox{0}.checked;
  bt_os_time{0}.disabled = !bt_os_chkbox{0}.checked;
}}

function ls_rel_radiobox{0}_onchange () {{
  ls_rel_dd{0}.disabled = !ls_rel_radiobox{0}.checked;
  ls_abs_ts{0}.disabled = ls_rel_radiobox{0}.checked;
}}
function ls_abs_radiobox{0}_onchange () {{
  ls_rel_dd{0}.disabled = ls_abs_radiobox{0}.checked;
  ls_abs_ts{0}.disabled = !ls_abs_radiobox{0}.checked;
}}

function ls_os_chkbox{0}_onchange () {{
  ls_os_plus{0}.disabled = !ls_os_chkbox{0}.checked;
  ls_os_minus{0}.disabled = !ls_os_chkbox{0}.checked;
  ls_os_time{0}.disabled = !ls_os_chkbox{0}.checked;
}}

function enable{0} () {{
    bt_on_radiobox{0}.disabled = 0;
    bt_off_radiobox{0}.disabled = 0;
    bt_rel_radiobox{0}.disabled = 0;
    bt_abs_radiobox{0}.disabled = 0;
    bt_rel_dd{0}.disabled = 0;
    bt_abs_ts{0}.disabled = 0;
    bt_os_chkbox{0}.disabled = 0;
    bt_os_plus{0}.disabled = 0;
    bt_os_minus{0}.disabled = 0;
    bt_os_time{0}.disabled = 0;
    ls_chkbox{0}.disabled = 0;
    ls_bfr_radiobox{0}.disabled = 0;
    ls_aft_radiobox{0}.disabled = 0;
    ls_rel_radiobox{0}.disabled = 0;
    ls_abs_radiobox{0}.disabled = 0;
    ls_rel_dd{0}.disabled = 0;
    ls_abs_ts{0}.disabled = 0;
    ls_os_chkbox{0}.disabled = 0;
    ls_os_plus{0}.disabled = 0;
    ls_os_minus{0}.disabled = 0;
    ls_os_time{0}.disabled = 0;

  bt_rel_radiobox{0}_onchange();
  bt_abs_radiobox{0}_onchange();
  bt_os_chkbox{0}_onchange();
  ls_rel_radiobox{0}_onchange();
  ls_abs_radiobox{0}_onchange();
  ls_os_chkbox{0}_onchange();
  ls_chkbox{0}_onchange();
}}

function disable_bt{0} () {{
    bt_on_radiobox{0}.disabled = 1;
    bt_off_radiobox{0}.disabled = 1;
    bt_rel_radiobox{0}.disabled = 1;
    bt_abs_radiobox{0}.disabled = 1;
    bt_rel_dd{0}.disabled = 1;
    bt_abs_ts{0}.disabled = 1;
    bt_os_chkbox{0}.disabled = 1;
    bt_os_plus{0}.disabled = 1;
    bt_os_minus{0}.disabled = 1;
    bt_os_time{0}.disabled = 1;
}}

function disable_ls{0} () {{
    ls_chkbox{0}.disabled = 1;
    ls_bfr_radiobox{0}.disabled = 1;
    ls_aft_radiobox{0}.disabled = 1;
    ls_rel_radiobox{0}.disabled = 1;
    ls_abs_radiobox{0}.disabled = 1;
    ls_rel_dd{0}.disabled = 1;
    ls_abs_ts{0}.disabled = 1;
    ls_os_chkbox{0}.disabled = 1;
    ls_os_plus{0}.disabled = 1;
    ls_os_minus{0}.disabled = 1;
    ls_os_time{0}.disabled = 1;
}}

function tb_state_active{0}_onchange () {{
  state_active{0}.checked = tb_state_active{0}.checked;
  if (tb_state_active{0}.checked)
  {{
      enable{0}();
  }}
  else
  {{
      disable_bt{0}();
      disable_ls{0}();
  }}
}}

function state_active{0}_onchange () {{
  tb_state_active{0}.checked = state_active{0}.checked;
  if (tb_state_active{0}.checked)
  {{
      enable{0}();
  }}
  else
  {{
      disable_bt{0}();
      disable_ls{0}();
  }}
}}

function ls_chkbox{0}_onchange () {{
  if (ls_chkbox{0}.checked)
  {{
    ls_os_chkbox{0}.disabled = 0;
    ls_bfr_radiobox{0}.disabled = 0;
    ls_aft_radiobox{0}.disabled = 0;
    ls_rel_radiobox{0}.disabled = 0;
    ls_abs_radiobox{0}.disabled = 0;
    ls_rel_dd{0}.disabled = !ls_rel_radiobox{0}.checked;
    ls_abs_ts{0}.disabled = !ls_abs_radiobox{0}.checked;
    ls_os_plus{0}.disabled = !ls_os_chkbox{0}.checked;
    ls_os_minus{0}.disabled = !ls_os_chkbox{0}.checked;
    ls_os_time{0}.disabled = !ls_os_chkbox{0}.checked;
  }}
  else
  {{
    disable_ls{0}();
  }}
}}

function onload{0} () {{
  tb_state_active{0}_onchange();
}}

bt_rel_radiobox{0}.onchange = function() {{bt_rel_radiobox{0}_onchange()}};
bt_abs_radiobox{0}.onchange = function() {{bt_abs_radiobox{0}_onchange()}};
bt_os_chkbox{0}.onchange = function() {{bt_os_chkbox{0}_onchange()}};
ls_rel_radiobox{0}.onchange = function() {{ls_rel_radiobox{0}_onchange()}};
ls_abs_radiobox{0}.onchange = function() {{ls_abs_radiobox{0}_onchange()}};
ls_os_chkbox{0}.onchange = function() {{ls_os_chkbox{0}_onchange()}};
ls_chkbox{0}.onchange = function() {{ls_chkbox{0}_onchange()}};
state_active{0}.onchange = function() {{state_active{0}_onchange()}};
tb_state_active{0}.onchange = function() {{tb_state_active{0}_onchange()}};


"""