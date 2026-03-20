import SwiftUI
import AVFoundation

struct ScanView: View {
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager
    @State private var selectedImage: UIImage?
    @State private var showCamera = false
    @State private var showLibrary = false
    @State private var showResult = false
    @State private var scanResult: ScanResult?
    @State private var isAnalyzing = false
    @State private var errorMessage: String?

    var c: AppColors { themeManager.colors }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Text(translations.t("scan.title")).font(.title2.bold()).foregroundColor(c.text)
                Text(translations.t("scan.subtitle")).font(.subheadline).foregroundColor(c.textSecondary)

                if let image = selectedImage {
                    Image(uiImage: image)
                        .resizable().scaledToFit()
                        .frame(maxHeight: 300)
                        .cornerRadius(14)
                        .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
                } else {
                    RoundedRectangle(cornerRadius: 14)
                        .fill(c.card)
                        .frame(height: 200)
                        .overlay(
                            VStack(spacing: 12) {
                                Image(systemName: "camera.fill").font(.system(size: 40)).foregroundColor(c.textSecondary)
                                Text(translations.t("scan.noimage")).font(.subheadline).foregroundColor(c.textSecondary)
                            }
                        )
                        .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border, style: StrokeStyle(lineWidth: 2, dash: [8])))
                }

                HStack(spacing: 12) {
                    Button { showCamera = true } label: {
                        Label(translations.t("scan.camera"), systemImage: "camera.fill")
                            .frame(maxWidth: .infinity).frame(height: 48)
                    }
                    .background(c.primary).foregroundColor(.white).cornerRadius(12)

                    Button { showLibrary = true } label: {
                        Label(translations.t("scan.gallery"), systemImage: "photo.on.rectangle")
                            .frame(maxWidth: .infinity).frame(height: 48)
                    }
                    .background(c.card).foregroundColor(c.text).cornerRadius(12)
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
                }

                if let error = errorMessage {
                    Text(error).font(.caption).foregroundColor(c.danger)
                }

                if selectedImage != nil {
                    Button {
                        Task { await analyzeImage() }
                    } label: {
                        if isAnalyzing {
                            HStack { ProgressView().tint(.white); Text("Analyzing...").foregroundColor(.white) }
                        } else {
                            Label(translations.t("scan.analyze"), systemImage: "wand.and.stars")
                        }
                    }
                    .frame(maxWidth: .infinity).frame(height: 50)
                    .background(c.success).foregroundColor(.white).cornerRadius(12).fontWeight(.bold)
                    .disabled(isAnalyzing)
                }
            }
            .padding(20)
        }
        .background(c.background.ignoresSafeArea())
        .sheet(isPresented: $showCamera) { ImagePicker(image: $selectedImage, sourceType: .camera) }
        .sheet(isPresented: $showLibrary) { ImagePicker(image: $selectedImage, sourceType: .photoLibrary) }
        .navigationDestination(isPresented: $showResult) {
            if let result = scanResult { ResultsView(result: result) }
        }
    }

    func analyzeImage() async {
        guard let image = selectedImage else { return }
        isAnalyzing = true; errorMessage = nil
        do {
            scanResult = try await APIService.shared.analyzeImage(image)
            showResult = true
        } catch { errorMessage = error.localizedDescription }
        isAnalyzing = false
    }
}

struct ImagePicker: UIViewControllerRepresentable {
    @Binding var image: UIImage?
    let sourceType: UIImagePickerController.SourceType

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = sourceType
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: ImagePicker
        init(_ parent: ImagePicker) { self.parent = parent }
        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]) {
            if let img = info[.originalImage] as? UIImage { parent.image = img }
            picker.dismiss(animated: true)
        }
        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) { picker.dismiss(animated: true) }
    }
}
