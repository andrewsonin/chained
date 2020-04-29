from typing import TypeVar

T = TypeVar('T')
M = TypeVar('M')

T_co = TypeVar('T_co', covariant=True)
M_co = TypeVar('M_co', covariant=True)

T_contra = TypeVar('T_contra', contravariant=True)
