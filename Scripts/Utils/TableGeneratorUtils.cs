using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Reflection;
using Godot;

public interface TableConfigElement
{
    string GetAttribute(string name);
    string GetText();
    List<TableConfigElement> GetElements();
}

public sealed class JsonConfigElement : TableConfigElement 
{
    private object jsonElement;

    public JsonConfigElement(object element)
    {
        jsonElement = element;
    }

    public string GetAttribute(string name)
    {
        var attribute = (jsonElement as Godot.Collections.Dictionary)[name];
        return attribute != null ? attribute.ToString() : null;
    }

    public string GetText()
    {
        return jsonElement.ToString();
    }
    public List<TableConfigElement> GetElements() 
    {
        List<TableConfigElement> elements = new List<TableConfigElement>();
        Godot.Collections.Array array = (Godot.Collections.Array)jsonElement;
        foreach(var element in array)
        {
            elements.Add(new JsonConfigElement(element));
        }
        return elements;
    }
}

public interface ITableGeneratorObject 
{
    void Read(TableConfigElement item);
}

public static class TableGeneratorUtility
{
    public static int Get(TableConfigElement element, string name, int _) 
    {
        string s = element.GetAttribute(name);
        return Convert(s, _);
    }

    public static float Get(TableConfigElement element, string name, float _) 
    {
        string s = element.GetAttribute(name);
        return Convert(s, _);
    }

    public static string Get(TableConfigElement element, string name, string _) 
    {
        string s = element.GetAttribute(name);
        return Convert(s, _);
    }

    public static bool Get(TableConfigElement element, string name, bool _) 
    {
        string s = element.GetAttribute(name);
        return Convert(s, _);
    }

    private static int Convert(TableConfigElement e, int _) 
    {
        return Convert(e.GetText(), _);
    }

    private static float Convert(TableConfigElement e, float _) 
    {
        return Convert(e.GetText(), _);
    }

    private static string Convert(TableConfigElement e, string _) 
    {
        return Convert(e.GetText(), _);
    }

    private static bool Convert(TableConfigElement e, bool _) 
    {
        return Convert(e.GetText(), _);
    }

    private static T Convert<T>(TableConfigElement e, T _) where T : ITableGeneratorObject, new() 
    {
        if (e == null) 
        {
            return default(T);
        }

        T t = new T();
        t.Read(e);
        return t;
    }

    private static int Convert(string s, int _)
    {
        if (string.IsNullOrEmpty(s)) 
        {
            return 0;
        }
        return int.Parse(s);
    }

    private static float Convert(string s, float _) 
    {
        if (string.IsNullOrEmpty(s)) 
        {
            return 0.0f;
        }
        return float.Parse(s);
    }

    private static string Convert(string s, string _) 
    {
        return s;
    }

    private static bool Convert(string s, bool _) 
    {
        if (string.IsNullOrEmpty(s)) 
        {
            return false;
        }
        return bool.Parse(s);
    }

    private static T[] GetArray<T>(TableConfigElement element, T[] _, Func<TableConfigElement, T, T> convert) 
    {
        List<T> list = new List<T>();
        var elements = element.GetElements();
        foreach (var node in elements) {
            list.Add(convert(node, default(T)));
        }
        return list.Count > 0 ? list.ToArray() : null;
    }

    private static TableConfigElement LoadRootElement(Stream stream) 
    {
        StreamReader reader = new StreamReader(stream, Encoding.UTF8);
        JSONParseResult result = JSON.Parse(reader.ReadToEnd());
        if (result.Result == null) {
            throw new Exception($"Could not parse json stream: {result.ErrorString}."); 
        }
        return new JsonConfigElement(result.Result);
    }

    public static T Load<T>(Stream stream) where T : ITableGeneratorObject, new() 
    {
        var root = LoadRootElement(stream);
        return Convert(root, default(T));
    }

    public static T[] Load<T>(Stream stream, string item) where T : ITableGeneratorObject, new() 
    {
        var root = LoadRootElement(stream);
        T[] items = GetArray(root, default(T[]), Convert);
        return items != null ? items : new T[0];
    }
}

public class GlobalTableSingle<T, DataT> 
    where T : GlobalTableSingle<T, DataT>, new()
    where DataT : class, ITableGeneratorObject, new()
{
	private const string exportedGlobalTablePath = "Design/DesignTables/Exported/GlobalTable";
    protected virtual string GetExportedTablePath()
    {
        return exportedGlobalTablePath;
    }

    public bool IsLoaded {get; private set;} = false;

    protected virtual void Init(DataT[] datas)  {}
    protected virtual void Init(DataT data) {}
    public virtual void Load() {}

    protected void Load(string tableName)
    { 
        string path = System.IO.Path.Combine(GetExportedTablePath(), tableName) + ".json";			
        System.IO.Stream stream = new System.IO.FileStream(path, System.IO.FileMode.Open, System.IO.FileAccess.Read, System.IO.FileShare.Read);
        if (stream.Length <= 0) {
            return;
        }

        Type typeInfo = typeof(DataT);
        MethodInfo[] methodInfos = typeInfo.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy);
        MethodInfo methodInfo = methodInfos.First(m => m.Name == "Load" && m.IsGenericMethodDefinition);
        methodInfo = methodInfo.MakeGenericMethod(typeof(DataT));

        // call Template::Load(Stream stream) 
        object[] parameters = {stream};
        object data = methodInfo.Invoke(null, parameters);

        if ((data as DataT[]) != null)
        {
            Init((data as DataT[]));
        } 
        else 
        {
            Init((DataT)data);
        }

        IsLoaded = true;
    }
}

public abstract class DesignTableSingle<T, KeyT, DataT> : GlobalTableSingle<T, DataT>
    where T : GlobalTableSingle<T, DataT>, new()
    where DataT : class, ITableGeneratorObject, new()
{
    public List<DataT> Datas = new List<DataT>();
    private Dictionary<KeyT, int> dict;

	private const string exportedDesignTablePath = "Design/DesignTables/Exported/DesignTable";
    protected override string GetExportedTablePath()
    {
        return exportedDesignTablePath;
    }

    protected abstract KeyT GetID(DataT item);
    protected override void Init(DataT[] datas)  
    {
        dict = new Dictionary<KeyT, int>(datas.Length);
        foreach (var data in datas) 
        {
            KeyT key = GetID(data);
            // 重复性检查在ExcelConvert节点就应该处理
            if (!dict.ContainsKey(key)) 
            {
                dict.Add(key, Datas.Count);
                Datas.Add(data);
            }   
        }
    }
    public bool IsExists(KeyT id)
    {
        return dict.ContainsKey(id);
    }

    public DataT GetData(KeyT id) 
    {
        if (!IsLoaded) {
            Load();
        }

        if (dict.TryGetValue(id, out int index)) {
            return Datas[index];
        }
        return default(DataT);
    }
}