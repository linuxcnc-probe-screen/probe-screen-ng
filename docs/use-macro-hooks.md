# Use Macro Hooks

To use macro hooks, you can do the following:

```shell
cd $HOME/linuxccnc/configs/MyConfigName
cp psng/macros/_psng_hook.ngc macros/_psng_hook.ngc
```

Now, edit the `macros/_psng_hook.ngc` file with the code you wish to run
at the start of each PSNG macro call. For example:

```gcode
o<_psng_hook> sub
#<hooked_macro> = #1

O100 if [#<hooked_macro> EQ 1]
; Do something specific to o<psng_manual_change> here
O100 return

O100 elseif  if [#<hooked_macro> EQ 2]
; Do something specific to o<psng_tool_diameter> here
O100 return
O100 endif

o<_psng_hook> endsub
M2
```
