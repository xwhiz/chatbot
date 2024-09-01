export default function MinFooter() {
  return (
    <footer className="relative pb-4">
      <div className="container mx-auto px-4">
        <div className="flex flex-wrap items-center md:justify-between justify-center">
          <div className="w-full md:w-4/12 px-4">
            <div className="text-sm text-slate-600 font-semibold py-1 text-center md:text-left">
              Copyright &copy; {new Date().getFullYear()}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
