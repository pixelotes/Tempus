function exportTableToCSV(filename, cortarUltimaColumna = true) {
    var csv = [];
    var table = document.querySelector("table");
    
    if (!table) {
        alert("No hay datos para exportar");
        return;
    }

    var rows = table.querySelectorAll("tr");
    
    for (var i = 0; i < rows.length; i++) {
        var row = [], cols = rows[i].querySelectorAll("td, th");
        
        // Determinamos hasta qué columna leer
        // Si cortarUltimaColumna es true, restamos 1 al total, si no, leemos todas
        var limit = cortarUltimaColumna ? cols.length - 1 : cols.length;

        for (var j = 0; j < limit; j++) {
            // Limpiamos el texto: quitamos saltos de línea y espacios dobles
            var data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, "").replace(/(\s\s+)/gm, " ").trim();
            
            // Escapamos las comillas dobles para formato CSV estándar
            data = data.replace(/"/g, '""');
            
            // Envolvemos en comillas
            row.push('"' + data + '"');
        }
        csv.push(row.join(","));
    }

    downloadCSV(csv.join("\n"), filename);
}

function downloadCSV(csv, filename) {
    var csvFile;
    var downloadLink;

    // BOM para que Excel abra correctamente caracteres UTF-8 (tildes, ñ)
    csvFile = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });

    downloadLink = document.createElement("a");
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = "none";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}