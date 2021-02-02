within HelloWorld;
model exportedModel
 extends Modelica.Blocks.Icons.Block;
  example mod(
    oveWriSet(uExt(y=oveWriSetPoint_u), activate(y=oveWriSetPoint_activate)),
    oveWriAct(uExt(y=oveWriActuatorSignal_u),activate(y=oveWriActuatorSignal_activate)),
    oveWriMea(uExt(y=oveWriMeasuredTemp_u), activate(y= oveWriMeasuredTemp_activate)))
    annotation (Placement(transformation(extent={{-10,-8},{10,12}})));
  Modelica.Blocks.Interfaces.RealInput oveWriSetPoint_u(unit="K")
    "Signal for overwrite block for set point" annotation (Placement(
        transformation(extent={{-120,58},{-100,78}}), iconTransformation(extent={{-120,58},
            {-100,78}})));
  Modelica.Blocks.Interfaces.BooleanInput oveWriSetPoint_activate
    "Activation for overwrite block for set point" annotation (Placement(
        transformation(extent={{-120,34},{-100,54}}), iconTransformation(extent={{-120,34},
            {-100,54}})));
  Modelica.Blocks.Interfaces.RealInput oveWriActuatorSignal_u(unit="K")
    "Signal for overwrite block for actuator signal" annotation (Placement(
        transformation(extent={{-120,12},{-100,32}}), iconTransformation(extent={{-120,12},
            {-100,32}})));
  Modelica.Blocks.Interfaces.BooleanInput oveWriActuatorSignal_activate
    "Activation for overwrite block for actuator signal" annotation (Placement(
        transformation(extent={{-120,-10},{-100,10}}),iconTransformation(extent={{-120,
            -10},{-100,10}})));
  Modelica.Blocks.Interfaces.RealOutput rea( unit="1")=mod.oveWriAct.y "Measured state variable"
    annotation (Placement(transformation(extent={{100,-10},{120,10}})));
  Modelica.Blocks.Interfaces.RealInput oveWriMeasuredTemp_u(unit="K")
    "Signal for overwrite block for measured signal" annotation (Placement(
        transformation(extent={{-120,-32},{-100,-12}}),
                                                      iconTransformation(extent={{-120,
            -32},{-100,-12}})));
  Modelica.Blocks.Interfaces.BooleanInput oveWriMeasuredTemp_activate
    "Activation for overwrite block for measured signal" annotation (Placement(
        transformation(extent={{-120,-54},{-100,-34}}), iconTransformation(
          extent={{-120,-54},{-100,-34}})));
 annotation (Placement(transformation(extent={{-8,-8},{12,12}})),
 Documentation(info="<html>  
   </html>",
   revisions="<html>
<ul>
<li>
January 21, 2021, by Hagar Elarga:<br/>
First implementation.
</li>
</ul>
</html>"));
end exportedModel;
