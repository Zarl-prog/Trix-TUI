class TrixIde < Formula
  include Language::Python::Virtualenv

  desc "A terminal-native IDE built with Textual"
  homepage "https://github.com/Zarl-prog/Trix-TUI"
  url "https://files.pythonhosted.org/packages/source/t/trix-ide/trix_ide-0.3.1.tar.gz"
  sha256 "d702b98060ba115ceacb076709a9fd1ccb230eaab753efd37a14b7299283871e"
  license "MIT"

  depends_on "python@3.14"

  resource "trix-ide" do
    url "https://files.pythonhosted.org/packages/source/t/trix-ide/trix_ide-0.3.1.tar.gz"
    sha256 "d702b98060ba115ceacb076709a9fd1ccb230eaab753efd37a14b7299283871e"
  end

  def install
    venv = virtualenv_create(libexec, "python3")
    venv.pip_install resources
    bin.install_symlink libexec/"bin/trix"
  end

  test do
    assert_match "trix", shell_output("#{bin}/trix --help", 1)
  end
end
