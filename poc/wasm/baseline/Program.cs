using System.Text;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using ImeWlConverter.Application.Bootstrap;
using ImeWlConverter.Abstractions.Contracts;
using ImeWlConverter.Abstractions.Options;
using WasmPoc;
Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
using var provider=ImeWlConverterBootstrapper.CreateServiceProvider(s=>s.AddSingleton<StreamConverter>());
var converter=provider.GetRequiredService<StreamConverter>();
if(args.Length==0){Console.WriteLine(await AdvancedChecks.Run(converter));return;}
if(args[0]=="canonical"){
 using var input=File.OpenRead(args[2]);var result=await converter.Importers.Single(x=>x.Metadata.Id==args[1]).ImportAsync(input);
 var rows=result.Entries.Select(x=>new{x.Word,code=x.Code?.GetPrimaryCode(" "),x.Rank}).OrderBy(x=>x.Word,StringComparer.Ordinal).ThenBy(x=>x.code,StringComparer.Ordinal);
 Console.WriteLine(JsonSerializer.Serialize(rows));return;
}
if(args[0]=="audit"){
 var report=new List<object>();
 foreach(var file in Directory.GetFiles(AppContext.BaseDirectory,"*.dll")){
 using var pe=new PEReader(File.OpenRead(file));if(!pe.HasMetadata)continue;var md=pe.GetMetadataReader();var native=new List<string>();var dynamic=new List<string>();
 foreach(var handle in md.MethodDefinitions){var m=md.GetMethodDefinition(handle);if((m.Attributes&System.Reflection.MethodAttributes.PinvokeImpl)!=0){var i=m.GetImport();native.Add(md.GetString(m.Name)+" -> "+md.GetString(md.GetModuleReference(i.Module).Name));}}
 foreach(var handle in md.MemberReferences){var member=md.GetMemberReference(handle);if(member.Parent.Kind!=HandleKind.TypeReference)continue;var type=md.GetTypeReference((TypeReferenceHandle)member.Parent);var full=md.GetString(type.Namespace)+"."+md.GetString(type.Name)+"."+md.GetString(member.Name);if(full.Contains("Reflection.Emit")||full.Contains("System.Linq.Expressions.Expression")||full.Contains("NativeLibrary")||full.Contains("Process.Start")||full.Contains("Thread.Start")||full.Contains("Assembly.Load"))dynamic.Add(full);}
 report.Add(new{assembly=Path.GetFileName(file),nativeImports=native,interestingReferences=dynamic.Distinct()});
 }
 Console.WriteLine(JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true}));
}
