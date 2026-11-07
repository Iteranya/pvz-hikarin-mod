
using System;
using System.IO;
using System.Reflection;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;

class P {
 static string GetString(MetadataReader r, StringHandle h) => r.GetString(h);
 static void Main(string[] args) {
  string path = args[0];
  using var fs = File.OpenRead(path);
  using var pe = new PEReader(fs);
  var md = pe.GetMetadataReader();
  string[] want = args.Length > 1 ? args[1].Split(',') : new[] { "LevelManager" };
  foreach (var th in md.TypeDefinitions) {
   var td = md.GetTypeDefinition(th);
   string name = GetString(md, td.Name);
   bool hit = false;
   foreach (var w in want) if (name.Contains(w)) hit = true;
   if (!hit) continue;
   string ns = GetString(md, td.Namespace);
   Console.WriteLine($"TYPE {ns}.{name}");
   foreach (var mh in td.GetMethods()) {
    var m = md.GetMethodDefinition(mh);
    Console.WriteLine("  M " + GetString(md, m.Name));
   }
   foreach (var fh in td.GetFields()) {
    var f = md.GetFieldDefinition(fh);
    Console.WriteLine("  F " + GetString(md, f.Name));
   }
   foreach (var ph in td.GetProperties()) {
    var p = md.GetPropertyDefinition(ph);
    Console.WriteLine("  P " + GetString(md, p.Name));
   }
  }
 }
}
