export const seasons = {
  winter: {
    name: "Winter",
    image:
      "https://images.pexels.com/photos/1366919/pexels-photo-1366919.jpeg?auto=compress&cs=tinysrgb&w=1920",
    gradient: {
      base: "from-slate-200 via-blue-100 to-slate-300",
      mesh1: "rgba(147, 197, 253, 0.3)", // Light blue
      mesh2: "rgba(191, 219, 254, 0.2)", // Pale blue
      mesh3: "rgba(165, 180, 252, 0.18)", // Lavender
    },
  },
  spring: {
    name: "Spring",
    image: "/public/spring.jpg",
    gradient: {
      base: "from-purple-200 via-pink-200 to-orange-100", // ✅ UPDATED - Purple mountains, pink flowers, warm sunset
      mesh1: "rgba(232, 121, 249, 0.28)", // ✅ Magenta/pink (flowers)
      mesh2: "rgba(196, 181, 253, 0.25)", // ✅ Purple (mountains)
      mesh3: "rgba(254, 215, 170, 0.22)", // ✅ Peach/orange (sunset)
    },
  },
  summer: {
    name: "Summer",
    image: "/public/summer.jpg",
    gradient: {
      base: "from-yellow-100 via-orange-50 to-yellow-200",
      mesh1: "rgba(253, 224, 71, 0.3)", // Yellow
      mesh2: "rgba(251, 146, 60, 0.2)", // Orange
      mesh3: "rgba(252, 211, 77, 0.18)", // Gold
    },
  },
  autumn: {
    name: "Autumn",
    image: "/public/autumn.jpg",
    gradient: {
      base: "from-orange-100 via-red-50 to-amber-200",
      mesh1: "rgba(251, 146, 60, 0.28)", // Orange
      mesh2: "rgba(239, 68, 68, 0.18)", // Red
      mesh3: "rgba(217, 119, 6, 0.2)", // Amber
    },
  },
};

export const seasonOrder = ["winter", "spring", "summer", "autumn"];
