//------------------------------------------------------------------------------
// <auto-generated>
//     This code was generated by a tool. Do not modify the file !!!!!
// </auto-generated>
//------------------------------------------------------------------------------

namespace Design
{
    public sealed class StaticGlobalTables
    {
        private static StaticGlobalTables instance = new StaticGlobalTables();
        public static StaticGlobalTables Instance {
            get {
                return instance;
            }
        }

        public PlayerAttributesTemplateManager PlayerAttributes {get; private set;} = new PlayerAttributesTemplateManager();


        public void LoadGlobalTables()
        {
            PlayerAttributes.Load();

        }
    }
}
