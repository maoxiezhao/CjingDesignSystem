using Godot;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;

public sealed class DesignManager : Spatial
{
	public override void _Ready()
	{
		LoadAllGlobalTables();

		GD.Print(Design.StaticGlobalTables.Instance.PlayerAttributes.Data.Gravity);
		GD.Print(Design.StaticGlobalTables.Instance.PlayerAttributes.Data.NormalSpeed);
		GD.Print(Design.StaticDesignTables.Instance.Test.GetData(2).MountId);
	}

	private void LoadAllGlobalTables()
	{
		Design.StaticGlobalTables.Instance.LoadGlobalTables();
	}
}
