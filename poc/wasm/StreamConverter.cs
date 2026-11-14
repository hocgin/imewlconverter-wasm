using System.Diagnostics;
using ImeWlConverter.Abstractions.Contracts;
using ImeWlConverter.Abstractions.Models;
using ImeWlConverter.Abstractions.Options;
using ImeWlConverter.Core.Pipeline;
namespace WasmPoc;

// Transport adapter only. Parsing, transformations and export remain upstream implementations.
public sealed class StreamConverter(IEnumerable<IFormatImporter> importers,
    IEnumerable<IFormatExporter> exporters, EntryTransformationService transform,
    FilterPipelineFactory filters)
{
    public IFormatImporter[] Importers { get; } = importers.ToArray();
    public IFormatExporter[] Exporters { get; } = exporters.ToArray();
    public async Task<ConversionOutput> ConvertAsync(IEnumerable<Stream> sources, string from, string to,
        ConversionOptions options, FilterConfig? filter = null,
        IProgress<ProgressInfo>? progress = null, CancellationToken ct = default)
    {
        var watch = Stopwatch.StartNew();
        var entries = new List<WordEntry>();
        var importErrors = new List<string>();
        foreach (var input in sources)
        {
            ct.ThrowIfCancellationRequested();
            progress?.Report(new(0, 1, "Import"));
            var result = await Importers.Single(x => x.Metadata.Id == from).ImportAsync(input, options.Import, ct);
            entries.AddRange(result.Entries);
            if (result.Errors is not null) importErrors.AddRange(result.Errors);
        }
        var imported = entries.Count;
        var transformed = await transform.ApplyAsync(entries, options, filters.Create(filter), progress, ct);
        ct.ThrowIfCancellationRequested();
        progress?.Report(new(0, transformed.Count, "Export"));
        using var output = new MemoryStream();
        var exported = await Exporters.Single(x => x.Metadata.Id == to).ExportAsync(transformed, output, options.Export, ct);
        return new(output.ToArray(), imported, exported.EntryCount, exported.ErrorCount, importErrors,
            watch.Elapsed.TotalMilliseconds, GC.GetTotalMemory(false), GC.GetGCMemoryInfo().HeapSizeBytes);
    }
}
public sealed record ConversionOutput(byte[] Data, int Imported, int Exported, int ExportErrors,
    List<string> ImportErrors, double ElapsedMs, long ManagedLiveBytesAfter, long ManagedHeapBytesAfter);
