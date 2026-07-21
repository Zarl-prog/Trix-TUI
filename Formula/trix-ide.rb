class TrixIde < Formula
  include Language::Python::Virtualenv

  desc "A terminal-native IDE built with Textual"
  homepage "https://github.com/Zarl-prog/Trix-TUI"
  url "https://github.com/Zarl-prog/Trix-TUI/archive/refs/tags/v0.3.1.tar.gz"
  sha256 "24f643890cef4faf28aa9869f10f45ec7ab44b33bd46fca306a72cf98caabd54"
  license "MIT"

  depends_on "python@3.14"

  def install
    venv = virtualenv_create(libexec)
    venv.pip_install "trix-ide"
    bin.install_symlink libexec/"bin/trix"
  end

  test do
    assert_match "trix", shell_output("#{bin}/trix --help", 1)
  end
end
