//------------------------------------------------------------------------------
// <auto-generated>
//     This code was generated by a tool. Do not modify the file !!!!!
// </auto-generated>
//------------------------------------------------------------------------------

namespace Design
{
    public sealed class StaticDesignTables
    {
        private static StaticDesignTables instance = new StaticDesignTables();
        public static StaticDesignTables Instance {
            get {
                return instance;
            }
        }

        public TestTemplateManager Test {get; private set;} = new TestTemplateManager();


        public void LoadDesignTables()
        {
            Test.Load();

        }
    }
}
