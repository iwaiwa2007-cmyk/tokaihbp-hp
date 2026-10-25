import PDFKit
import AppKit
let path = CommandLine.arguments[1]
let doc = PDFDocument(url: URL(fileURLWithPath:path))!
for i in 0..<doc.pageCount {
 let im = doc.page(at:i)!.thumbnail(of:NSSize(width:1200,height:1700),for:.mediaBox)
 let rep=NSBitmapImageRep(data:im.tiffRepresentation!)!
 try rep.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:"tmp/pdfs/verified-\(i+1).png"))
}
