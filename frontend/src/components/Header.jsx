function Header() {
  return (
    <header className="bg-blue-600 text-white p-4 shadow-lg">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center">
          Daily Integral Challenge
        </h1>
        <p className="text-center text-blue-100 mt-2">
          Solve today's calculus problem
        </p>
      </div>
    </header>
  );
}

export default Header;