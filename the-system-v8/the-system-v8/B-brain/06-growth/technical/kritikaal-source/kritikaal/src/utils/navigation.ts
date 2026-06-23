/**
 * Navigation utility for smooth scrolling to sections
 * Handles both on-page and cross-page navigation
 */

export const scrollToSection = (sectionId: string) => {
  const element = document.getElementById(sectionId);
  if (element) {
    // Add offset for fixed navbar (adjust the offset value based on your navbar height)
    const navbarHeight = 160; // Adjust this to match your navbar height
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - navbarHeight;

    window.scrollTo({
      top: offsetPosition,
      behavior: "smooth"
    });
  }
};

export const navigateToSection = (
  navigate: (path: string) => void,
  currentPath: string,
  sectionId: string
) => {
  if (currentPath === '/') {
    // Already on home page, just scroll
    scrollToSection(sectionId);
  } else {
    // Navigate to home page first, then scroll
    navigate('/');
    // Wait for navigation to complete before scrolling
    setTimeout(() => {
      scrollToSection(sectionId);
    }, 100);
  }
};

/**
 * Checks if a path is a section link (starts with #)
 */
export const isSectionLink = (path: string): boolean => {
  return path.startsWith('#');
};

/**
 * Gets section ID from path
 * Examples: "#hero" -> "hero", "/#services" -> "services"
 */
export const getSectionId = (path: string): string => {
  return path.replace(/^#/, '').replace(/^\/#/, '');
};
