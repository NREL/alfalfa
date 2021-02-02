within HelloWorld;
model example "Simple controller"

  extends Modelica.Blocks.Icons.Block;

  Buildings.Controls.OBC.CDL.Continuous.PID conPI(controllerType=Modelica.Blocks.Types.SimpleController.PI,
    yMax=1,
    yMin=0)  "Controller"
    annotation (Placement(transformation(extent={{-10,10},{10,30}})));
  Modelica.Blocks.Sources.Constant TSet(k=20 + 273.15) "Set point"
    annotation (Placement(transformation(extent={{-90,10},{-70,30}})));
  Buildings.Utilities.IO.SignalExchange.Overwrite oveWriSet(description="First order system control setpoint",
     u(
      min=-10,
      max=10,
      unit="1")) "Overwrite block for setpoint"
    annotation (Placement(transformation(extent={{-50,10},{-30,30}})));
  Buildings.Utilities.IO.SignalExchange.Overwrite
            oveWriAct(description="First order system input", u(
      min=-10,
      max=10,
      unit="1")) "Overwrite block for actuator signal"
    annotation (Placement(transformation(extent={{32,10},{52,30}})));
  Buildings.Utilities.IO.SignalExchange.Overwrite oveWriMea(description="Measured overwrite")
    "Overwrite block for setpoint"
    annotation (Placement(transformation(extent={{-42,-50},{-22,-30}})));
  Modelica.Blocks.Sources.Constant TMod(k=20 + 273.15) "Model temperature"
    annotation (Placement(transformation(extent={{-90,-50},{-70,-30}})));
equation
  connect(TSet.y, oveWriSet.u)
    annotation (Line(points={{-69,20},{-52,20}}, color={0,0,127}));
  connect(conPI.u_s, oveWriSet.y)
    annotation (Line(points={{-12,20},{-29,20}},color={0,0,127}));
  connect(conPI.y, oveWriAct.u)
    annotation (Line(points={{12,20},{30,20}}, color={0,0,127}));
  connect(oveWriMea.y, conPI.u_m)
    annotation (Line(points={{-21,-40},{0,-40},{0,8}}, color={0,0,127}));
  connect(oveWriMea.u, TMod.y)
    annotation (Line(points={{-44,-40},{-69,-40}}, color={0,0,127}));
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
end example;
